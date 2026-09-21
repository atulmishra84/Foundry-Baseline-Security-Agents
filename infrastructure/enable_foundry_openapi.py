"""Attach authenticated runtime OpenAPI tools to all four Foundry agents."""

from __future__ import annotations

import json
import os
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import OpenApiConnectionAuthDetails, OpenApiConnectionSecurityScheme, OpenApiTool
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

SHARED = """Scope is only the authorized in-repo HealthcareAIAssistant demo.
Always call foundry_runtime OpenAPI tools. Do not invent results.
Call runLifecycle with retest=true, then summarize the tool JSON.
You may call health first and listArtifacts after.
Do not change Entra identities or containment settings."""

SPECS = [
    {
        "name": "ai-security-orchestrator",
        "description": "Runs the authorized lifecycle via the Container App and summarizes results",
        "instructions": f"""You coordinate the Foundary AI security assessment on Azure AI Foundry.
If the user asks to run, assess, or review the authorized healthcare demo:
1. Call health.
2. Call runLifecycle with retest=true.
3. Summarize findings, remediations, validation count, incidents, retest_blocked, and correlation_id from the tool only.
{SHARED}""",
    },
    {
        "name": "ai-security-engineer",
        "description": "Discovers, assesses, and remediates via the authorized runtime",
        "instructions": f"""You are the AI Security Engineer.
If asked to assess the authorized healthcare demo, call runLifecycle, then explain assets, findings, OWASP IDs, and remediations from the tool output only.
{SHARED}""",
    },
    {
        "name": "ai-red-team",
        "description": "Confirms T-001 only via the authorized runtime",
        "instructions": f"""You record whether the authorized demo control held.
If asked to review or confirm the demo, call runLifecycle and report exploitability and retest_blocked from the tool output only.
Do not propose new techniques. Do not target any other system.
{SHARED}""",
    },
    {
        "name": "ai-runtime-soc",
        "description": "Raises incidents from authorized runtime evidence",
        "instructions": f"""You are the AI Runtime SOC analyst.
If asked to review telemetry or incidents, call runLifecycle and report incident count and severity from the tool output. Containment stays human-approved.
{SHARED}""",
    },
]


def runtime_tool() -> OpenApiTool:
    conn = os.getenv("FOUNDRY_RUNTIME_CONNECTION_ID", "").strip()
    if not conn:
        raise SystemExit("FOUNDRY_RUNTIME_CONNECTION_ID missing. Run infrastructure/ensure_runtime_connection.py")
    spec = json.loads((ROOT / "services" / "foundry_runtime" / "openapi.json").read_text(encoding="utf-8"))
    auth = OpenApiConnectionAuthDetails(
        security_scheme=OpenApiConnectionSecurityScheme(connection_id=conn)
    )
    return OpenApiTool(
        name="foundry_runtime",
        description="Authorized Foundary lifecycle runtime (health, runLifecycle, listArtifacts).",
        spec=spec,
        auth=auth,
    )


def main() -> None:
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    tools = list(runtime_tool().definitions)
    existing = {agent.name: agent for agent in client.list_agents()}
    for spec in SPECS:
        current = existing.get(spec["name"])
        if not current:
            print("missing", spec["name"], "- run deploy_agents.py / foundry_orchestrator.py first")
            continue
        agent = client.update_agent(
            agent_id=current.id,
            model=MODEL,
            name=spec["name"],
            description=spec["description"],
            instructions=spec["instructions"],
            tools=tools,
        )
        print("updated", agent.name, agent.id)


if __name__ == "__main__":
    main()
