"""Keep the orchestrator agent present, then attach authenticated runtime OpenAPI tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
os.chdir(ROOT)

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "937d718f-c0b8-458e-9f26-7d69e169c671")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-ai-security-platform")
PROJECT_NAME = os.getenv("AZURE_AI_PROJECT", "project-security-agents")
PROJECT_ENDPOINT = (
    f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{SUBSCRIPTION_ID}"
    f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices"
    f"/workspaces/{PROJECT_NAME}"
)
MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
ORCHESTRATOR_NAME = "ai-security-orchestrator"


def main() -> None:
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    existing = next((a for a in client.list_agents() if a.name == ORCHESTRATOR_NAME), None)
    if not existing:
        agent = client.create_agent(
            model=MODEL,
            name=ORCHESTRATOR_NAME,
            instructions="Call foundry_runtime.runLifecycle for the authorized demo only.",
            description="Foundry orchestrator",
        )
        print("created", agent.name, agent.id)
        agent_id = agent.id
    else:
        print("exists", existing.name, existing.id)
        agent_id = existing.id

    env_path = ROOT / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    lines = [ln for ln in lines if not ln.startswith("AI_SECURITY_ORCHESTRATOR_ID=")]
    lines.append(f"AI_SECURITY_ORCHESTRATOR_ID={agent_id}")
    env_path.write_text("\n".join(lines) + "\n")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import enable_foundry_openapi
    import ensure_runtime_connection

    ensure_runtime_connection.main()
    enable_foundry_openapi.main()


if __name__ == "__main__":
    main()
