"""
Update Foundry agents with live tools and run an end-to-end live test.
Run from repo root: python3 infrastructure/live_test_agents.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    AgentThreadCreationOptions,
    FunctionTool,
    ThreadMessageOptions,
    ToolSet,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
load_dotenv(ROOT / ".env")

from tools.foundry.agent_tools import (
    analyze_latest_evidence,
    assess_discovered_asset,
    discover_target,
    generate_finding_remediations,
    list_sot_threats,
    validate_authorized_demo,
)

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "937d718f-c0b8-458e-9f26-7d69e169c671")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-ai-security-platform")
PROJECT_NAME = os.getenv("AZURE_AI_PROJECT", "project-security-agents")
PROJECT_ENDPOINT = (
    f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{SUBSCRIPTION_ID}"
    f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices"
    f"/workspaces/{PROJECT_NAME}"
)

AGENT_SPECS = [
    {
        "env": "AI_SECURITY_ENGINEER_ID",
        "name": "ai-security-engineer",
        "functions": {
            discover_target,
            assess_discovered_asset,
            generate_finding_remediations,
            list_sot_threats,
        },
        "prompt": (
            "Live test on the authorized local Healthcare AI Assistant only. "
            "Call discover_target, then assess_discovered_asset, then generate_finding_remediations. "
            "Summarize finding counts and OWASP IDs. Do not invent extra targets."
        ),
    },
    {
        "env": "AI_RED_TEAM_ID",
        "name": "ai-red-team",
        "functions": {validate_authorized_demo, list_sot_threats},
        "prompt": (
            "Live test: call validate_authorized_demo once. That tool only hits the authorized "
            "local HealthcareAIAssistant. Do not propose or run any other attack. "
            "Report exploitability from the tool result."
        ),
    },
    {
        "env": "AI_RUNTIME_SOC_ID",
        "name": "ai-runtime-soc",
        "functions": {analyze_latest_evidence, list_sot_threats},
        "prompt": (
            "Live test: call analyze_latest_evidence and explain the incident severity and lineage. "
            "Recommend human-approved response only. Do not execute containment yourself."
        ),
    },
]


def _toolset(functions: set) -> ToolSet:
    toolset = ToolSet()
    toolset.add(FunctionTool(functions))
    return toolset


def _assistant_text(client: AgentsClient, thread_id: str) -> str:
    messages = list(client.messages.list(thread_id=thread_id))
    parts = []
    for message in messages:
        if getattr(message, "role", None) != "assistant":
            continue
        for item in getattr(message, "text_messages", []) or []:
            text = getattr(getattr(item, "text", None), "value", None)
            if text:
                parts.append(text)
        if not parts and getattr(message, "content", None):
            parts.append(str(message.content))
    return "\n".join(parts) or "(no assistant text)"


def main() -> None:
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    results = []

    for spec in AGENT_SPECS:
        agent_id = os.getenv(spec["env"])
        if not agent_id:
            raise SystemExit(f"Missing {spec['env']} in .env — run infrastructure/deploy_agents.py")

        toolset = _toolset(spec["functions"])
        client.enable_auto_function_calls(toolset)
        client.update_agent(
            agent_id=agent_id,
            toolset=toolset,
            description=f"Live-test enabled {spec['name']}",
        )
        print(f"[live] invoking {spec['name']} ({agent_id})")

        run = client.create_thread_and_process_run(
            agent_id=agent_id,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content=spec["prompt"])]
            ),
            toolset=toolset,
        )
        text = _assistant_text(client, run.thread_id)
        record = {
            "agent": spec["name"],
            "agent_id": agent_id,
            "run_id": run.id,
            "thread_id": run.thread_id,
            "status": run.status,
            "reply": text[:4000],
        }
        results.append(record)
        print(f"  status={run.status}")

    out = ROOT / "output" / "foundry-live-test.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"saved {out}")
    failed = [item for item in results if str(item["status"]) not in {"completed", "RunStatus.COMPLETED", "COMPLETED"}]
    if failed:
        raise SystemExit(f"Live test failed for: {[item['agent'] for item in failed]}")
    print("All Foundry agents completed a live test run.")


if __name__ == "__main__":
    main()
