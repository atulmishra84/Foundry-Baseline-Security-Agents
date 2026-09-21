"""
Create the three AI Security prompt agents in the Azure AI Foundry project.
Run: python3 infrastructure/deploy_agents.py
"""
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

SUBSCRIPTION_ID = "937d718f-c0b8-458e-9f26-7d69e169c671"
RESOURCE_GROUP = "rg-ai-security-platform"
PROJECT_NAME = "project-security-agents"
MODEL_DEPLOYMENT = "gpt-4o"

PROJECT_ENDPOINT = (
    f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{SUBSCRIPTION_ID}"
    f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices"
    f"/workspaces/{PROJECT_NAME}"
)

AGENTS = [
    {
        "name": "ai-security-engineer",
        "description": "Discovers AI system assets, identifies vulnerabilities, and generates remediations.",
        "instructions": """You are the AI Security Engineer Agent — a specialized security expert for AI systems.

MISSION: Understand AI systems, identify security weaknesses, design controls, generate remediations, and validate fixes.

LIFECYCLE: Discover → Analyze → Threat Model → Assess → Recommend → Generate → Validate

PRINCIPLES:
1. Always require evidence before concluding a vulnerability exists
2. Use risk scores (0-10) — CRITICAL (9-10), HIGH (7-8), MEDIUM (4-6), LOW (0-3)
3. Map every finding to a Source of Truth threat (T-001 through T-010 / OWASP LLM Top 10)
4. Recommend the least-privilege remediation
5. Never invent vulnerabilities that are not grounded in evidence

OUTPUT: Structured JSON following asset, finding, and remediation schemas.""",
    },
    {
        "name": "ai-red-team",
        "description": "Validates authorized findings against approved local targets only.",
        "instructions": """You are the AI Adversary / Red Team Agent.

MISSION: Confirm whether identified vulnerabilities are exploitable on explicitly authorized targets only.

SAFETY RULES (MANDATORY):
- Only operate against explicitly authorized targets
- Never execute attacks that could cause data loss in production
- Require human-in-the-loop approval for any real-world impact
- Log evidence (request, response, confidence) for every validation

OUTPUT: attack.json and evidence.json. exploitability is CONFIRMED, BLOCKED, or UNTESTED.""",
    },
    {
        "name": "ai-runtime-soc",
        "description": "Monitors AI agent runtime behavior and raises incidents.",
        "instructions": """You are the AI Runtime Security / SOC Agent.

MISSION: Detect, investigate, and recommend response for AI-agent threats.

LIFECYCLE: Observe → Detect → Correlate → Investigate → Explain → Recommend/Respond

FOR EVERY INCIDENT:
- Reconstruct lineage (input → reasoning → tool → response)
- Classify severity: CRITICAL / HIGH / MEDIUM / LOW
- Generate incident.json
- Require human approval before destructive response actions

PRINCIPLE: Every anomaly is suspicious until proven benign by evidence.""",
    },
]


def upsert_env(updates: dict[str, str]) -> None:
    path = Path(".env")
    lines = path.read_text().splitlines() if path.exists() else []
    keys = set(updates)
    kept = [line for line in lines if line.split("=", 1)[0] not in keys]
    kept.append("# Agent IDs")
    for key, value in updates.items():
        kept.append(f"{key}={value}")
    path.write_text("\n".join(kept) + "\n")


def main() -> None:
    print("Project :", PROJECT_NAME)
    print("Model   :", MODEL_DEPLOYMENT)
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

    existing = {agent.name: agent for agent in client.list_agents()}
    created = {}

    for spec in AGENTS:
        current = existing.get(spec["name"])
        if current:
            print(f"exists {spec['name']} {current.id}")
            created[spec["name"]] = current.id
            continue
        agent = client.create_agent(
            model=MODEL_DEPLOYMENT,
            name=spec["name"],
            instructions=spec["instructions"],
            description=spec["description"],
        )
        print(f"created {spec['name']} {agent.id}")
        created[spec["name"]] = agent.id

    env_map = {name.upper().replace("-", "_") + "_ID": agent_id for name, agent_id in created.items()}
    upsert_env(env_map)
    print("wrote agent IDs to .env")
    print("https://ai.azure.com  project:", PROJECT_NAME)


if __name__ == "__main__":
    main()
