import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.sot.loader import frameworks


def owasp_catalog() -> dict:
    for item in frameworks():
        if item.get("framework_id") == "OWASP-LLM-2025":
            return item
    catalogs = frameworks()
    return catalogs[0] if catalogs else {"entries": []}


def build_coverage(finding_file: str) -> list[dict]:
    findings = []
    if os.path.exists(finding_file):
        with open(finding_file, encoding="utf-8") as handle:
            findings = json.load(handle)

    hit = set()
    for finding in findings:
        hit.update(finding.get("owasp_llm") or [])

    rows = []
    for entry in owasp_catalog().get("entries") or []:
        status = "COVERED" if entry["id"] in hit else "MAPPED"
        if entry["id"] in {"LLM04", "LLM08"} and entry["id"] not in hit:
            status = "NOT_APPLICABLE"
        rows.append(
            {
                "owasp_id": entry["id"],
                "name": entry["name"],
                "threat_id": entry["threat_id"],
                "control_id": entry["control_id"],
                "status": status,
            }
        )
    return rows


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    rows = build_coverage("output/finding.json")
    with open("output/owasp-coverage.json", "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    print(f"[SoT] OWASP coverage rows: {len(rows)}")
