# Where the agents appear in Azure AI Foundry

The three agents are **not** on the Azure OpenAI account (`aoai-ai-security-*`).
They live on the **Foundry project** `project-security-agents` (under hub `hub-ai-security`).

If you open the OpenAI resource, the hub only, or a different subscription/directory, the Agents list is empty. The API still lists them:

- `ai-security-engineer`
- `ai-red-team`
- `ai-runtime-soc`

## Open this project (use this URL)

[Security Agents Project in Azure AI Foundry](https://ai.azure.com/build/agents?wsid=/subscriptions/937d718f-c0b8-458e-9f26-7d69e169c671/resourceGroups/rg-ai-security-platform/providers/Microsoft.MachineLearningServices/workspaces/project-security-agents&tid=c087fa1c-7d10-4bd7-8956-a7958bb4fed6)

Backup (Azure Machine Learning studio):

[Same project in ML Studio](https://ml.azure.com/?wsid=/subscriptions/937d718f-c0b8-458e-9f26-7d69e169c671/resourceGroups/rg-ai-security-platform/providers/Microsoft.MachineLearningServices/workspaces/project-security-agents&tid=c087fa1c-7d10-4bd7-8956-a7958bb4fed6)

## Clicks if the URL does not land correctly

1. Sign in at https://ai.azure.com with the same tenant that `az account show` uses.
2. Confirm directory **and** subscription `937d718f-c0b8-458e-9f26-7d69e169c671`.
3. Open **All resources** / **Hubs and projects**.
4. Open hub **hub-ai-security**, then project **project-security-agents** (friendly name: Security Agents Project).
5. In the project, open **Build** → **Agents** (or **Assistants** in older layouts). Do not stop on the hub overview.

## Prove they exist without the portal

```bash
python3 infrastructure/deploy_agents.py
```

To make Playground run the real loop (not just chat):

```bash
python3 infrastructure/ensure_runtime_connection.py
python3 infrastructure/enable_foundry_openapi.py
python3 infrastructure/playground_smoke.py
```

In the project Agents playground, open **ai-security-orchestrator** (or Engineer / Red Team / SOC).

Use this prompt only (Azure may block words like attack, exploit, red team, or hijack):

`Assess the authorized healthcare demo. Call runLifecycle with retest true. Summarize finding counts and whether retest_blocked is true.`

The agent calls the Container App through a project connection. It does not store the Bearer token in the prompt.

That command lists existing agents if they are already created. Laptop-hosted function tools:

```bash
AZURE_LOG_LEVEL=warning python3 infrastructure/live_test_agents.py
```
