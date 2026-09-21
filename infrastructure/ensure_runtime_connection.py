"""Create a CustomKeys project connection that injects Authorization: Bearer <token>."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "937d718f-c0b8-458e-9f26-7d69e169c671")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-ai-security-platform")
PROJECT_NAME = os.getenv("AZURE_AI_PROJECT", "project-security-agents")
CONN_NAME = "foundry-runtime"
TARGET = os.getenv(
    "FOUNDRY_RUNTIME_URL",
    "https://ca-ai-security-runtime.wonderfulriver-296ea5d0.eastus.azurecontainerapps.io",
)


def connection_id() -> str:
    return (
        f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.MachineLearningServices/workspaces/{PROJECT_NAME}"
        f"/connections/{CONN_NAME}"
    )


def main() -> None:
    token = os.getenv("FOUNDRY_RUNTIME_TOKEN", "").strip()
    if not token:
        raise SystemExit("FOUNDRY_RUNTIME_TOKEN is missing in .env")

    url = (
        f"https://management.azure.com{connection_id()}?api-version=2024-07-01-preview"
    )
    body = {
        "properties": {
            "authType": "CustomKeys",
            "category": "CustomKeys",
            "credentials": {"keys": {"Authorization": f"Bearer {token}"}},
            "target": TARGET,
            "isSharedToAll": True,
            "metadata": {"purpose": "Foundry OpenAPI tool for the authorized lifecycle runtime"},
        }
    }
    payload_path = ROOT / "output" / ".runtime-connection.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(body))
    try:
        subprocess.run(
            ["az", "rest", "--method", "put", "--url", url, "--body", f"@{payload_path}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        if payload_path.exists():
            payload_path.unlink()

    env_path = ROOT / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    lines = [ln for ln in lines if not ln.startswith("FOUNDRY_RUNTIME_CONNECTION_ID=")]
    lines.append(f"FOUNDRY_RUNTIME_CONNECTION_ID={connection_id()}")
    env_path.write_text("\n".join(lines) + "\n")
    print("connection", CONN_NAME)
    print(connection_id())


if __name__ == "__main__":
    main()
