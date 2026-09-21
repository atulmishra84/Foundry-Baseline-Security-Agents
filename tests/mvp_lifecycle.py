import json
import os
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from tools.a2a.bus import publish
from tools.runtime.monitor import analyze_evidence
from tools.security.assessor import assess_asset
from tools.security.attacker import execute_attack
from tools.security.discovery import discover_assets
from tools.security.remediator import generate_remediations
from tools.dashboard.export_powerbi import export_dataset
from tools.security.retest import retest
from tools.sot.framework_coverage import build_framework_coverage
from tools.sot.owasp_coverage import build_coverage


def main():
    print("Starting multi-agent A2A lifecycle...")
    os.makedirs("output", exist_ok=True)
    correlation_id = str(uuid.uuid4())

    asset = discover_assets("tests/vulnerable-app/app.py")
    with open("output/asset.json", "w", encoding="utf-8") as handle:
        json.dump(asset, handle, indent=2)
    publish(
        from_agent="security-engineer",
        to_agent="security-engineer",
        intent="DISCOVERY_COMPLETE",
        correlation_id=correlation_id,
        payload_ref="output/asset.json",
        summary=asset.get("name", ""),
    )

    findings = assess_asset("output/asset.json")
    with open("output/finding.json", "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2)
    publish(
        from_agent="security-engineer",
        to_agent="red-team",
        intent="ASSESS_COMPLETE",
        correlation_id=correlation_id,
        payload_ref="output/finding.json",
        summary=f"{len(findings)} findings",
    )

    remediations = generate_remediations("output/finding.json")
    with open("output/remediation.json", "w", encoding="utf-8") as handle:
        json.dump(remediations, handle, indent=2)
    publish(
        from_agent="security-engineer",
        to_agent="orchestrator",
        intent="REMEDIATION_READY",
        correlation_id=correlation_id,
        payload_ref="output/remediation.json",
        summary=f"{len(remediations)} remediations",
    )

    attacks, evidence = execute_attack("output/finding.json", "tests/vulnerable-app/app.py")
    with open("output/attack.json", "w", encoding="utf-8") as handle:
        json.dump(attacks, handle, indent=2)
    with open("output/evidence.json", "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2)
    publish(
        from_agent="red-team",
        to_agent="runtime-soc",
        intent="ATTACK_COMPLETE",
        correlation_id=correlation_id,
        payload_ref="output/evidence.json",
        summary=f"{len(attacks)} attack records",
    )

    incidents = analyze_evidence("output/evidence.json")
    with open("output/incident.json", "w", encoding="utf-8") as handle:
        json.dump(incidents, handle, indent=2)
    publish(
        from_agent="runtime-soc",
        to_agent="security-engineer",
        intent="INCIDENT_RAISED",
        correlation_id=correlation_id,
        payload_ref="output/incident.json",
        summary=f"{len(incidents)} incidents",
    )

    coverage = build_coverage("output/finding.json")
    with open("output/owasp-coverage.json", "w", encoding="utf-8") as handle:
        json.dump(coverage, handle, indent=2)
    with open("output/framework-coverage.json", "w", encoding="utf-8") as handle:
        json.dump(build_framework_coverage("output/finding.json"), handle, indent=2)
    retest_result = retest("output/finding.json")
    with open("output/retest.json", "w", encoding="utf-8") as handle:
        json.dump(retest_result, handle, indent=2)
    export_dataset("output", meta={"correlation_id": correlation_id})
    print("[Orchestrator] A2A lifecycle complete. Artifacts in output/.")


if __name__ == "__main__":
    main()
