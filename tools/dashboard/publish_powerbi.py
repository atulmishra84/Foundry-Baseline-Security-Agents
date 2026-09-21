"""Create or reuse a Power BI workspace and push the risk dataset from CSV."""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.powerbi.com/v1.0/myorg"
WORKSPACE = os.getenv("FOUNDRY_POWERBI_WORKSPACE", "Foundary AI Security")
DATASET = "FoundaryRiskFindings"


def _token() -> str:
    return DefaultAzureCredential(exclude_interactive_browser_credential=False).get_token(
        "https://analysis.windows.net/powerbi/api/.default"
    ).token


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def ensure_workspace(token: str) -> str:
    groups = requests.get(f"{API}/groups", headers=_headers(token), timeout=30)
    groups.raise_for_status()
    for item in groups.json().get("value") or []:
        if item.get("name") == WORKSPACE:
            return item["id"]
    created = requests.post(
        f"{API}/groups?workspaceV2=True",
        headers=_headers(token),
        data=json.dumps({"name": WORKSPACE}),
        timeout=30,
    )
    created.raise_for_status()
    return created.json()["id"]


def ensure_dataset(token: str, workspace_id: str) -> str:
    existing = requests.get(f"{API}/groups/{workspace_id}/datasets", headers=_headers(token), timeout=30)
    existing.raise_for_status()
    for item in existing.json().get("value") or []:
        if item.get("name") == DATASET:
            return item["id"]
    body = {
        "name": DATASET,
        "defaultMode": "Push",
        "tables": [
            {
                "name": "Findings",
                "columns": [
                    {"name": "finding_id", "dataType": "string"},
                    {"name": "asset", "dataType": "string"},
                    {"name": "risk_score", "dataType": "double"},
                    {"name": "risk_level", "dataType": "string"},
                    {"name": "threats", "dataType": "string"},
                    {"name": "owasp_llm", "dataType": "string"},
                    {"name": "mitre_atlas", "dataType": "string"},
                    {"name": "nist_ai_rmf", "dataType": "string"},
                ],
            }
        ],
    }
    created = requests.post(
        f"{API}/groups/{workspace_id}/datasets",
        headers=_headers(token),
        data=json.dumps(body),
        timeout=30,
    )
    created.raise_for_status()
    return created.json()["id"]


def push_rows(token: str, workspace_id: str, dataset_id: str, csv_path: Path) -> int:
    rows = []
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    score = float(row.get("risk_score") or 0)
                except ValueError:
                    score = 0.0
                rows.append(
                    {
                        "finding_id": row.get("finding_id") or "",
                        "asset": row.get("asset") or "",
                        "risk_score": score,
                        "risk_level": row.get("risk_level") or "",
                        "threats": row.get("threats") or "",
                        "owasp_llm": row.get("owasp_llm") or "",
                        "mitre_atlas": row.get("mitre_atlas") or "",
                        "nist_ai_rmf": row.get("nist_ai_rmf") or "",
                    }
                )
    requests.delete(
        f"{API}/groups/{workspace_id}/datasets/{dataset_id}/tables/Findings/rows",
        headers=_headers(token),
        timeout=30,
    )
    if rows:
        posted = requests.post(
            f"{API}/groups/{workspace_id}/datasets/{dataset_id}/tables/Findings/rows",
            headers=_headers(token),
            data=json.dumps({"rows": rows}),
            timeout=30,
        )
        posted.raise_for_status()
    return len(rows)


def publish(csv_path: Path | None = None) -> dict:
    token = _token()
    workspace_id = ensure_workspace(token)
    dataset_id = ensure_dataset(token, workspace_id)
    count = push_rows(token, workspace_id, dataset_id, csv_path or ROOT / "output" / "powerbi-risk-dataset.csv")
    url = f"https://app.powerbi.com/groups/{workspace_id}/datasets/{dataset_id}/details"
    return {"workspace": WORKSPACE, "workspace_id": workspace_id, "dataset_id": dataset_id, "rows": count, "url": url}


if __name__ == "__main__":
    try:
        result = publish()
    except Exception as exc:
        print(f"Power BI publish failed: {exc}", file=sys.stderr)
        print("Need a Power BI / Fabric license and permission to create workspaces.")
        sys.exit(1)
    print(json.dumps(result, indent=2))
