import json
import os
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.foundry.openai_client import chat_json
from tools.sot.loader import frameworks, threats


def _risk_level(score: float) -> str:
    if score >= 9:
        return "CRITICAL"
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def assess_asset(asset_file: str) -> list[dict]:
    if not os.path.exists(asset_file):
        raise FileNotFoundError(f"Asset file {asset_file} not found.")

    with open(asset_file, encoding="utf-8") as handle:
        asset = json.load(handle)

    findings = []
    catalog = {item["threat_id"]: item for item in threats()}
    owasp = []
    atlas_by_threat = {}
    nist_by_threat: dict[str, list[str]] = {}
    for fw in frameworks():
        fid = fw.get("framework_id")
        if fid == "OWASP-LLM-2025":
            owasp = fw.get("entries") or []
        elif fid == "MITRE-ATLAS":
            for entry in fw.get("entries") or []:
                atlas_by_threat[entry["threat_id"]] = entry["id"]
        elif fid == "NIST-AI-RMF":
            for fn in fw.get("functions") or []:
                for tid in fn.get("maps_to") or []:
                    nist_by_threat.setdefault(tid, []).append(fn["id"])

    rules = [
        (
            asset.get("asset_type") == "Agent",
            "T-001",
            ["Asset is a direct-prompt-processing agent with no documented guardrails."],
            ["Implement input validation (CTRL-001)"],
        ),
        (
            "patient_search" in asset.get("discovered_tools", []),
            "T-002",
            ["patient_search can return clinical records; no authorization field on the asset."],
            ["Add output filtering and authorization (CTRL-003)"],
        ),
        (
            asset.get("asset_type") == "Agent",
            "T-005",
            ["Tool results are returned to the caller without an output-encoding control."],
            ["Encode and validate model/tool output (CTRL-003)"],
        ),
        (
            "system-admin-identity" in asset.get("identities", []),
            "T-006",
            ["Agent uses highly privileged 'system-admin-identity'."],
            ["Apply least privilege RBAC (CTRL-005)."],
        ),
        (
            asset.get("asset_type") == "Agent",
            "T-007",
            ["No system-prompt isolation or leak-prevention control recorded."],
            ["Separate secrets from prompts (CTRL-001)."],
        ),
        (
            asset.get("asset_type") == "Agent",
            "T-009",
            ["No grounding or citation requirement recorded for clinical answers."],
            ["Require grounded responses (CTRL-006)."],
        ),
        (
            asset.get("asset_type") == "Agent",
            "T-010",
            ["No token budget or tool-call cap recorded on the runtime."],
            ["Add rate limits (CTRL-007)."],
        ),
        (
            not any(d for d in asset.get("dependencies", []) if d not in {"json", "logging", "os", "sys"}),
            "T-003",
            ["Supply-chain inventory lacks pinned third-party model, framework, or MCP dependencies."],
            ["Pin and review dependencies (CTRL-004)."],
        ),
    ]

    for applies, threat_id, evidence, recommendations in rules:
        if not applies:
            continue
        threat = catalog.get(threat_id, {})
        score = float(threat.get("risk_score_baseline", 7.0))
        owasp_id = threat.get("owasp_llm")
        findings.append(
            {
                "finding_id": f"FND-{str(uuid.uuid4())[:8]}",
                "asset": asset.get("asset_id"),
                "risk_score": score,
                "risk_level": _risk_level(score),
                "threats": [threat_id],
                "controls": [],
                "recommendations": recommendations,
                "evidence": evidence,
                "owasp_llm": [owasp_id] if owasp_id else [],
                "mitre_atlas": [atlas_by_threat[threat_id]] if threat_id in atlas_by_threat else [],
                "nist_ai_rmf": nist_by_threat.get(threat_id, []),
            }
        )

    llm = chat_json(
        "You are the AI Security Engineer. Return JSON {\"notes\": string} only. Do not invent new vulnerabilities.",
        json.dumps({"asset": asset, "findings": findings, "owasp": owasp}, indent=2),
    )
    if llm and llm.get("notes"):
        for finding in findings:
            finding["evidence"].append(f"Foundry review: {llm['notes']}")

    return findings


if __name__ == "__main__":
    asset_target = "output/asset.json"
    os.makedirs("output", exist_ok=True)
    findings = assess_asset(asset_target)
    output_file = os.path.join("output", "finding.json")
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2)
    print(f"[Security Engineer] Assessment complete. {len(findings)} findings saved to {output_file}")
