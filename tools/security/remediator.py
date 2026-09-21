import json
import os
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.foundry.openai_client import chat_json
from tools.sot.loader import controls


CONTROL_BY_THREAT = {
    "T-001": ("CTRL-001-Input-Validation", "POLICY"),
    "T-002": ("CTRL-003-Output-Filtering", "CODE_PATCH"),
    "T-003": ("CTRL-004-Dependency-Pinning", "CONFIGURATION"),
    "T-005": ("CTRL-003-Output-Filtering", "CODE_PATCH"),
    "T-006": ("CTRL-005-Least-Privilege", "RBAC"),
    "T-007": ("CTRL-001-Input-Validation", "POLICY"),
    "T-009": ("CTRL-006-Grounding", "POLICY"),
    "T-010": ("CTRL-007-Rate-Limits", "CONFIGURATION"),
}


def generate_remediations(finding_file: str) -> list[dict]:
    if not os.path.exists(finding_file):
        raise FileNotFoundError(f"Finding file {finding_file} not found.")

    with open(finding_file, encoding="utf-8") as handle:
        findings = json.load(handle)

    control_docs = {item["control_id"]: item for item in controls()}
    remediations = []

    for finding in findings:
        threat = (finding.get("threats") or ["T-001"])[0]
        control_id, rem_type = CONTROL_BY_THREAT.get(threat, ("CTRL-001-Input-Validation", "POLICY"))
        control = control_docs.get(control_id, {})
        remediations.append(
            {
                "remediation_id": f"REM-{str(uuid.uuid4())[:8]}",
                "finding_id": finding["finding_id"],
                "description": control.get("description", finding.get("recommendations", [""])[0]),
                "type": rem_type,
                "content": control.get("name", control_id),
                "validation_test": f"Re-assess {threat} after applying {control_id}.",
            }
        )

    llm = chat_json(
        "You are the AI Security Engineer. Return JSON {\"priorities\": [finding_id,...]} only.",
        json.dumps(findings, indent=2),
    )
    if llm and isinstance(llm.get("priorities"), list):
        order = {fid: idx for idx, fid in enumerate(llm["priorities"])}
        remediations.sort(key=lambda item: order.get(item["finding_id"], 99))

    return remediations


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    remediations = generate_remediations("output/finding.json")
    output_file = os.path.join("output", "remediation.json")
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(remediations, handle, indent=2)
    print(f"[Security Engineer] {len(remediations)} remediations saved to {output_file}")
