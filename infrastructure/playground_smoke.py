"""Playground-equivalent: ask the orchestrator to run the authorized lifecycle via OpenAPI."""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "937d718f-c0b8-458e-9f26-7d69e169c671")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-ai-security-platform")
PROJECT_NAME = os.getenv("AZURE_AI_PROJECT", "project-security-agents")
PROJECT_ENDPOINT = (
    f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{SUBSCRIPTION_ID}"
    f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices"
    f"/workspaces/{PROJECT_NAME}"
)


def main() -> None:
    agent_id = os.environ["AI_SECURITY_ORCHESTRATOR_ID"]
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    run = client.create_thread_and_process_run(
        agent_id=agent_id,
        thread=AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role="user",
                    content=(
                        "Assess the authorized healthcare demo. "
                        "Call runLifecycle with retest true. "
                        "Summarize finding counts and whether retest_blocked is true."
                    ),
                )
            ]
        ),
    )
    print("run", run.status, getattr(run, "last_error", None))
    messages = list(client.messages.list(thread_id=run.thread_id))
    for message in messages:
        if message.role == "assistant" and message.text_messages:
            print(message.text_messages[-1].text.value)
            break


if __name__ == "__main__":
    main()
