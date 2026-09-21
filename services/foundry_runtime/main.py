"""Foundry-adjacent runtime: run the closed loop and persist to hub storage."""

from __future__ import annotations

import json
import os
import sys
import uuid

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from tools.a2a.bus import publish
from tools.dashboard.export_powerbi import export_dataset
from tools.foundry.blob_store import write_bytes, write_json
from tools.runtime.monitor import analyze_evidence
from tools.security.assessor import assess_asset
from tools.security.attacker import execute_attack
from tools.security.discovery import discover_assets
from tools.security.remediator import generate_remediations
from tools.security.retest import retest
from tools.sot.framework_coverage import build_framework_coverage
from tools.sot.owasp_coverage import build_coverage

ALLOWED_ARTIFACTS = {
    "asset.json",
    "finding.json",
    "remediation.json",
    "owasp-coverage.json",
    "framework-coverage.json",
    "attack.json",
    "evidence.json",
    "incident.json",
    "retest.json",
    "executive-dashboard.html",
    "powerbi-risk-dataset.csv",
}


class NewlineJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return (json.dumps(content) + "\n").encode("utf-8")


app = FastAPI(title="Foundry AI Security Runtime", version="1.1.0", default_response_class=NewlineJSONResponse)


def _require_token(authorization: str | None) -> None:
    expected = os.getenv("FOUNDRY_RUNTIME_TOKEN", "")
    if not expected:
        return
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _refresh_dashboard(correlation_id: str = "") -> str:
    export_dataset(os.path.join(ROOT, "output"), meta={"correlation_id": correlation_id})
    html_path = os.path.join(ROOT, "output", "executive-dashboard.html")
    csv_path = os.path.join(ROOT, "output", "powerbi-risk-dataset.csv")
    if os.path.exists(csv_path):
        write_bytes("powerbi-risk-dataset.csv", open(csv_path, "rb").read())
    return write_bytes("executive-dashboard.html", open(html_path, "rb").read())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "ecosystem": "azure-ai-foundry", "version": "1.1.0"}


@app.get("/dashboard")
def dashboard(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    path = _refresh_dashboard()
    return FileResponse(path, media_type="text/html")


@app.get("/v1/artifacts")
def list_artifacts(authorization: str | None = Header(default=None)) -> dict:
    _require_token(authorization)
    output = os.path.join(ROOT, "output")
    present = sorted(name for name in ALLOWED_ARTIFACTS if os.path.exists(os.path.join(output, name)))
    return {"artifacts": present}


@app.get("/v1/artifacts/{name}")
def get_artifact(name: str, authorization: str | None = Header(default=None)):
    _require_token(authorization)
    if name not in ALLOWED_ARTIFACTS:
        raise HTTPException(status_code=404, detail="Unknown artifact")
    path = os.path.join(ROOT, "output", name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Artifact not generated yet")
    media = "text/html" if name.endswith(".html") else "application/json" if name.endswith(".json") else "text/csv"
    return FileResponse(path, media_type=media)


@app.get("/openapi-runtime.json")
def openapi_runtime():
    path = os.path.join(os.path.dirname(__file__), "openapi.json")
    return FileResponse(path, media_type="application/json")


@app.post("/v1/lifecycle")
def run_lifecycle(
    retest_controls: bool = Query(True, alias="retest"),
    authorization: str | None = Header(default=None),
) -> dict:
    _require_token(authorization)
    correlation_id = str(uuid.uuid4())
    artifacts: list[str] = []

    asset = discover_assets(os.path.join(ROOT, "tests", "vulnerable-app", "app.py"))
    artifacts.append(write_json("asset.json", asset))
    publish(
        from_agent="security-engineer",
        to_agent="red-team",
        intent="DISCOVERY_COMPLETE",
        correlation_id=correlation_id,
        payload_ref="asset.json",
        summary=asset.get("name", ""),
    )

    findings = assess_asset(os.path.join(ROOT, "output", "asset.json"))
    artifacts.append(write_json("finding.json", findings))
    remediations = generate_remediations(os.path.join(ROOT, "output", "finding.json"))
    artifacts.append(write_json("remediation.json", remediations))
    coverage = build_coverage(os.path.join(ROOT, "output", "finding.json"))
    artifacts.append(write_json("owasp-coverage.json", coverage))
    artifacts.append(
        write_json("framework-coverage.json", build_framework_coverage(os.path.join(ROOT, "output", "finding.json")))
    )

    attacks, evidence = execute_attack(
        os.path.join(ROOT, "output", "finding.json"),
        os.path.join(ROOT, "tests", "vulnerable-app", "app.py"),
    )
    artifacts.append(write_json("attack.json", attacks))
    artifacts.append(write_json("evidence.json", evidence))
    publish(
        from_agent="red-team",
        to_agent="runtime-soc",
        intent="ATTACK_COMPLETE",
        correlation_id=correlation_id,
        payload_ref="evidence.json",
        summary=f"{len(attacks)} attacks",
    )

    incidents = analyze_evidence(os.path.join(ROOT, "output", "evidence.json"))
    artifacts.append(write_json("incident.json", incidents))
    publish(
        from_agent="runtime-soc",
        to_agent="security-engineer",
        intent="INCIDENT_RAISED",
        correlation_id=correlation_id,
        payload_ref="incident.json",
        summary=f"{len(incidents)} incidents",
    )

    retest_blocked = None
    if retest_controls:
        result = retest(os.path.join(ROOT, "output", "finding.json"))
        artifacts.append(write_json("retest.json", result))
        retest_blocked = bool(result.get("blocked"))

    artifacts.append(_refresh_dashboard(correlation_id))
    return {
        "correlation_id": correlation_id,
        "findings": len(findings),
        "remediations": len(remediations),
        "attacks": len(attacks),
        "incidents": len(incidents),
        "retest_blocked": retest_blocked,
        "dashboard": "/dashboard",
        "artifacts": artifacts,
    }
