"""Runtime SOC Monitoring Engine with multi-vector threat and anomaly detection."""

from __future__ import annotations

import json
import os
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.foundry.openai_client import chat_json
from tools.prod.controls import apply_containment, redact_text


def analyze_evidence(evidence_file: str) -> list[dict]:
    if not os.path.exists(evidence_file):
        raise FileNotFoundError(f"Evidence file {evidence_file} not found.")

    with open(evidence_file, encoding="utf-8") as handle:
        evidence_log = json.load(handle)

    incidents = []
    for log in evidence_log:
        response = str(log.get("response", ""))
        request = str(log.get("request", ""))
        tool_name = str(log.get("tool", ""))

        summary = {}
        try:
            summary = json.loads(response) if response.startswith("{") else {}
        except json.JSONDecodeError:
            summary = {}

        bulk_dump = bool(summary.get("bulk_dump")) or ("P1001" in response and "P1002" in response)
        is_elevated_identity = bool(summary.get("elevated")) or ("system-admin" in response.lower())

        incident = None

        if bulk_dump:
            incident = {
                "incident_id": f"INC-{str(uuid.uuid4())[:8]}",
                "title": "Suspected Prompt Injection leading to Data Exfiltration",
                "status": "NEW",
                "severity": "CRITICAL",
                "lineage": [
                    "User Input",
                    "HealthcareAIAssistant processing",
                    f"{tool_name} execution",
                    "Database dump",
                ],
                "related_events": [log["evidence_id"]],
                "recommendation": (
                    "Block the requesting user, disable the patient_search tool temporarily, "
                    "and alert the Security Engineer for remediation."
                ),
            }
        elif is_elevated_identity and "identity" in tool_name.lower():
            incident = {
                "incident_id": f"INC-{str(uuid.uuid4())[:8]}",
                "title": "Excessive Agency: Unconstrained Administrator Identity Detected at Runtime",
                "status": "NEW",
                "severity": "CRITICAL",
                "lineage": [
                    "Runtime Identity Initialization",
                    "Assigned 'system-admin-identity'",
                    "Execution context holds unrestricted administrative permissions",
                ],
                "related_events": [log["evidence_id"]],
                "recommendation": (
                    "Revoke administrator role and assign scoped least-privilege managed identity (CTRL-005)."
                ),
            }

        if not incident:
            continue

        llm = chat_json(
            "You are the Runtime SOC agent. Return JSON {\"recommendation\": string} only. Do not include PHI.",
            json.dumps(
                {
                    "request": redact_text(request),
                    "response_preview": summary or redact_text(response[:200]),
                },
                indent=2,
            ),
        )
        if llm and llm.get("recommendation"):
            incident["recommendation"] = llm["recommendation"]
        incident = apply_containment(incident)
        incidents.append(incident)

    return incidents


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    incidents = analyze_evidence("output/evidence.json")
    output_file = os.path.join("output", "incident.json")
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(incidents, handle, indent=2)
    print(f"[Runtime SOC] Monitoring complete. {len(incidents)} incidents generated.")
