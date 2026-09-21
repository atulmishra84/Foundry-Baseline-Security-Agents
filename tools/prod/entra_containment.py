"""Disable the allowlisted demo service principal via Microsoft Graph.

Never targets arbitrary users or customer tenants. The object id must match
config/production.json containment_service_principal_id.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from azure.identity import DefaultAzureCredential

from tools.prod.controls import load_config

GRAPH = "https://graph.microsoft.com/v1.0"


def _token() -> str:
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    return cred.get_token("https://graph.microsoft.com/.default").token


def allowed_sp_id() -> str:
    cfg = load_config()
    return str(os.getenv("FOUNDRY_CONTAINMENT_SP_ID") or cfg.get("containment_service_principal_id") or "").strip()


def set_service_principal_enabled(object_id: str, enabled: bool, token: str | None = None) -> dict[str, Any]:
    allowed = allowed_sp_id()
    if not allowed:
        raise PermissionError("No containment_service_principal_id configured.")
    if object_id != allowed:
        raise PermissionError("Refusing Graph change: object id is not the allowlisted demo SP.")
    headers = {
        "Authorization": f"Bearer {token or _token()}",
        "Content-Type": "application/json",
    }
    response = requests.patch(
        f"{GRAPH}/servicePrincipals/{object_id}",
        headers=headers,
        data=json.dumps({"accountEnabled": enabled}),
        timeout=30,
    )
    if response.status_code not in (200, 204):
        raise RuntimeError(f"Graph PATCH failed: {response.status_code} {response.text[:400]}")
    return {"object_id": object_id, "accountEnabled": enabled}


def execute_approved_containment(incident: dict) -> dict:
    sp_id = allowed_sp_id()
    if not sp_id:
        incident["containment"] = {
            "executed": False,
            "approved": True,
            "reason": "Approval present but containment_service_principal_id is empty. Run infrastructure/setup_entra_containment.sh",
        }
        return incident
    try:
        result = set_service_principal_enabled(sp_id, enabled=False)
        incident["containment"] = {
            "executed": True,
            "approved": True,
            "action": "disable_service_principal",
            "target": result["object_id"],
            "reason": "Demo Healthcare tool SP disabled via Microsoft Graph.",
        }
    except Exception as exc:
        incident["containment"] = {
            "executed": False,
            "approved": True,
            "reason": f"Graph containment failed: {exc}",
        }
    return incident
