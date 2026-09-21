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
        summary = {}
        try:
            summary = json.loads(response) if response.startswith("{") else {}
        except json.JSONDecodeError:
            summary = {}
        bulk_dump = bool(summary.get("bulk_dump")) or ("P1001" in response and "P1002" in response)
        if not bulk_dump:
            continue

        incident = {
            "incident_id": f"INC-{str(uuid.uuid4())[:8]}",
            "title": "Suspected Prompt Injection leading to Data Exfiltration",
            "status": "NEW",
            "severity": "CRITICAL",
            "lineage": [
                "User Input",
                "HealthcareAIAssistant processing",
                "patient_search tool execution with None parameters",
                "Database dump",
            ],
            "related_events": [log["evidence_id"]],
            "recommendation": (
                "Block the requesting user, disable the patient_search tool temporarily, "
                "and alert the Security Engineer for remediation."
            ),
        }
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
