"""Local tools Foundry agents may call during live tests. Authorized demo only."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.runtime.monitor import analyze_evidence
from tools.security.assessor import assess_asset
from tools.security.attacker import execute_attack
from tools.security.discovery import discover_assets
from tools.security.remediator import generate_remediations
from tools.sot.loader import threats
from tools.sot.owasp_coverage import build_coverage


def _write(name: str, payload) -> str:
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    path = os.path.join(ROOT, "output", name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def discover_target() -> str:
    """Discover the authorized local Healthcare AI Assistant and write asset.json."""
    asset = discover_assets(os.path.join(ROOT, "tests", "vulnerable-app", "app.py"))
    path = _write("asset.json", asset)
    return json.dumps({"output": path, "asset": asset})


def assess_discovered_asset() -> str:
    """Assess output/asset.json against the Source of Truth and write finding.json."""
    findings = assess_asset(os.path.join(ROOT, "output", "asset.json"))
    path = _write("finding.json", findings)
    coverage = build_coverage(path)
    _write("owasp-coverage.json", coverage)
    return json.dumps({"output": path, "finding_count": len(findings)})


def generate_finding_remediations() -> str:
    """Generate remediations from output/finding.json and write remediation.json."""
    remediations = generate_remediations(os.path.join(ROOT, "output", "finding.json"))
    path = _write("remediation.json", remediations)
    return json.dumps({"output": path, "remediation_count": len(remediations)})


def validate_authorized_demo() -> str:
    """Validate T-001 only against the authorized local healthcare demo. Do not target any other system."""
    attacks, evidence = execute_attack(
        os.path.join(ROOT, "output", "finding.json"),
        os.path.join(ROOT, "tests", "vulnerable-app", "app.py"),
    )
    _write("attack.json", attacks)
    _write("evidence.json", evidence)
    return json.dumps(
        {
            "target": "authorized local HealthcareAIAssistant only",
            "attacks": len(attacks),
            "exploitability": [item.get("exploitability") for item in attacks],
        }
    )


def analyze_latest_evidence() -> str:
    """Analyze output/evidence.json and write incident.json."""
    incidents = analyze_evidence(os.path.join(ROOT, "output", "evidence.json"))
    path = _write("incident.json", incidents)
    return json.dumps(
        {
            "output": path,
            "incident_count": len(incidents),
            "incidents": [
                {
                    "incident_id": item.get("incident_id"),
                    "title": item.get("title"),
                    "severity": item.get("severity"),
                    "status": item.get("status"),
                    "lineage": item.get("lineage"),
                    "recommendation": item.get("recommendation"),
                }
                for item in incidents
            ],
        }
    )


def list_sot_threats() -> str:
    """Return the Source of Truth threat catalog (id, name, OWASP mapping)."""
    rows = [
        {
            "threat_id": item.get("threat_id"),
            "name": item.get("name"),
            "owasp_llm": item.get("owasp_llm"),
        }
        for item in threats()
    ]
    return json.dumps(rows)
