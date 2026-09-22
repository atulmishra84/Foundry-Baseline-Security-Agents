"""Foundry-adjacent runtime: run the closed loop and persist to hub storage."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sys
import uuid

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# ── Application Insights tracing (optional — only active when env var is set) ──
_APPINSIGHTS_CS = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
if _APPINSIGHTS_CS:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=_APPINSIGHTS_CS)
    except ImportError:
        pass  # Package not installed in local dev — silently skip

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("foundry-runtime")
except ImportError:
    _tracer = None  # type: ignore[assignment]

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


app = FastAPI(title="Foundry AI Security Runtime", version="1.2.0", default_response_class=NewlineJSONResponse)


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


class ContainmentApprovalRequest(BaseModel):
    incident_id: str
    approved_by: str = "security-engineer-ui"
    action: str = "disable_service_principal"


@app.get("/v1/stages")
def get_stages(authorization: str | None = Header(default=None)) -> dict:
    _require_token(authorization)
    output = os.path.join(ROOT, "output")

    asset_path = os.path.join(output, "asset.json")
    finding_path = os.path.join(output, "finding.json")
    attack_path = os.path.join(output, "attack.json")
    incident_path = os.path.join(output, "incident.json")
    retest_path = os.path.join(output, "retest.json")

    has_asset = os.path.exists(asset_path)
    has_finding = os.path.exists(finding_path)
    has_attack = os.path.exists(attack_path)
    has_incident = os.path.exists(incident_path)
    has_retest = os.path.exists(retest_path)

    findings_count = len(json.load(open(finding_path, encoding="utf-8"))) if has_finding else 0
    attacks_count = len(json.load(open(attack_path, encoding="utf-8"))) if has_attack else 0
    incidents_count = len(json.load(open(incident_path, encoding="utf-8"))) if has_incident else 0
    retest_data = json.load(open(retest_path, encoding="utf-8")) if has_retest else {}

    retest_status = "BLOCKED" if retest_data.get("blocked") else ("OPEN" if has_retest else "PENDING")

    stages = [
        {
            "id": 1,
            "name": "Asset Discovery",
            "agent": "AI Security Engineer",
            "status": "COMPLETE" if has_asset else "PENDING",
            "summary": "Asset boundaries and tool registries mapped" if has_asset else "Awaiting discovery",
            "artifact": "asset.json",
        },
        {
            "id": 2,
            "name": "Threat Assessment",
            "agent": "AI Security Engineer",
            "status": "COMPLETE" if has_finding else "PENDING",
            "summary": f"{findings_count} findings evaluated against OWASP/ATLAS/NIST" if has_finding else "Awaiting assessment",
            "artifact": "finding.json",
        },
        {
            "id": 3,
            "name": "Red Team Validation",
            "agent": "AI Red Team",
            "status": "COMPLETE" if has_attack else "PENDING",
            "summary": f"{attacks_count} adversarial attacks tested with evidence" if has_attack else "Awaiting red team run",
            "artifact": "attack.json",
        },
        {
            "id": 4,
            "name": "Runtime SOC Monitoring",
            "agent": "AI Runtime SOC",
            "status": "COMPLETE" if has_incident else "PENDING",
            "summary": f"{incidents_count} incidents raised with event lineage" if has_incident else "Awaiting telemetry analysis",
            "artifact": "incident.json",
        },
        {
            "id": 5,
            "name": "Remediation & Retest",
            "agent": "AI Security Orchestrator",
            "status": retest_status,
            "summary": "Controls validated and held on hardened build" if retest_data.get("blocked") else "Awaiting retest verification",
            "artifact": "retest.json",
        },
    ]
    return {"stages": stages}


@app.post("/v1/containment/approve")
def approve_containment(
    req: ContainmentApprovalRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    _require_token(authorization)
    approvals_dir = os.path.join(ROOT, "output", "approvals")
    os.makedirs(approvals_dir, exist_ok=True)
    approval_file = os.path.join(approvals_dir, f"{req.incident_id}.json")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "incident_id": req.incident_id,
        "approved_by": req.approved_by,
        "action": req.action,
        "timestamp": timestamp,
    }
    with open(approval_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Emit containment approval trace event to Application Insights
    if _tracer:
        with _tracer.start_as_current_span("containment.approve") as span:
            span.set_attribute("incident_id", req.incident_id)
            span.set_attribute("approved_by", req.approved_by)
            span.set_attribute("action", req.action)
            span.set_attribute("timestamp", timestamp)

    return {
        "status": "APPROVED",
        "incident_id": req.incident_id,
        "approval_file": approval_file,
        "approved_by": req.approved_by,
        "action": req.action,
    }


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

    span_ctx = _tracer.start_as_current_span("lifecycle.run") if _tracer else None  # type: ignore[union-attr]
    try:
        span = span_ctx.__enter__() if span_ctx else None  # type: ignore[union-attr]
        if span and hasattr(span, "set_attribute"):
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("retest", retest_controls)

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

        if span and hasattr(span, "set_attribute"):
            span.set_attribute("findings", len(findings))
            span.set_attribute("attacks", len(attacks))
            span.set_attribute("incidents", len(incidents))
            span.set_attribute("retest_blocked", str(retest_blocked))
    finally:
        if span_ctx:
            span_ctx.__exit__(None, None, None)  # type: ignore[union-attr]

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
