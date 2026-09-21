"""Production controls: allowlist, PHI redaction, SOC approval."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "production.json"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def authorized_paths() -> set[str]:
    cfg = load_config()
    return {
        os.path.abspath(os.path.join(ROOT, item["path"]))
        for item in cfg.get("authorized_targets", [])
    }


def assert_authorized_target(target_app: str) -> None:
    resolved = os.path.abspath(target_app if os.path.isabs(target_app) else os.path.join(os.getcwd(), target_app))
    allowed = authorized_paths()
    if resolved not in allowed:
        raise PermissionError(
            f"Target {resolved} is not on the production allowlist. "
            "Refusing to run Red Team validation."
        )


def redact_text(value: str) -> str:
    text = value
    text = re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[REDACTED_NAME]", text)
    text = re.sub(
        r"\b(Hypertension|Diabetes|Asthma|Lisinopril|Metformin|Albuterol)\b",
        "[REDACTED_CLINICAL]",
        text,
        flags=re.I,
    )
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    return text


def summarize_response(raw: str) -> dict:
    record_ids = re.findall(r"P\d{4}", raw)
    bulk = len(set(record_ids)) >= 2
    return {
        "bulk_dump": bulk,
        "record_ids": sorted(set(record_ids)),
        "response": "[REDACTED]",
        "char_length": len(raw),
    }


def approval_path(incident_id: str) -> Path:
    return ROOT / "output" / "approvals" / f"{incident_id}.json"


def containment_allowed(incident_id: str) -> bool:
    if os.getenv("FOUNDRY_SOC_EXECUTE", "").lower() == "true":
        path = approval_path(incident_id)
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("approved_by") and data.get("action"))
    return False


def apply_containment(incident: dict) -> dict:
    incident_id = incident["incident_id"]
    if not containment_allowed(incident_id):
        incident["containment"] = {
            "executed": False,
            "reason": "Human approval file missing. Write output/approvals/{incident_id}.json with approved_by and action.",
        }
        return incident
    from tools.prod.entra_containment import execute_approved_containment

    return execute_approved_containment(incident)
