# How to test all three Foundry agents

Use the **same Azure account** that deployed `rg-ai-security-platform`. Testing only targets the **authorized local** Healthcare AI Assistant in this repo.

## 1. One-time setup

In a terminal, from the repo root (`Foundary`):

```bash
cd /Users/mac/Foundary
az account show
python3 -m pip install -r requirements.txt
```

Confirm `.env` exists and includes `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and the three agent IDs (`AI_SECURITY_ENGINEER_ID`, `AI_RED_TEAM_ID`, `AI_RUNTIME_SOC_ID`).

If agent IDs are missing:

```bash
python3 infrastructure/deploy_agents.py
```

## 2. Run the full live test (recommended)

```bash
AZURE_LOG_LEVEL=warning python3 infrastructure/live_test_agents.py
```

Wait until you see:

```text
[live] invoking ai-security-engineer ...
  status=RunStatus.COMPLETED
[live] invoking ai-red-team ...
  status=RunStatus.COMPLETED
[live] invoking ai-runtime-soc ...
  status=RunStatus.COMPLETED
All Foundry agents completed a live test run.
```

Red Team will print a local demo log (`Agent hijacked via prompt injection`). That is expected for this authorized target.

## 3. Check results

| Check | File / place |
|---|---|
| Agent replies | `output/foundry-live-test.json` |
| Engineer output | `output/asset.json`, `output/finding.json`, `output/remediation.json` |
| Red Team output | `output/attack.json`, `output/evidence.json` |
| SOC output | `output/incident.json` |
| Dashboard | `output/executive-dashboard.html` |

Open `output/foundry-live-test.json` and confirm each `"status": "completed"`.

**Pass criteria**

- Engineer: findings count greater than 0  
- Red Team: exploitability `CONFIRMED` (or `BLOCKED` if you later harden the demo)  
- SOC: at least one incident with severity set  

## 4. Optional: test in the Azure portal

1. Open the **project** (not the OpenAI resource):  
   https://ai.azure.com/build/agents?wsid=/subscriptions/937d718f-c0b8-458e-9f26-7d69e169c671/resourceGroups/rg-ai-security-platform/providers/Microsoft.MachineLearningServices/workspaces/project-security-agents&tid=c087fa1c-7d10-4bd7-8956-a7958bb4fed6
2. If the list is empty, you are on the hub or the OpenAI account. Switch to project **project-security-agents**.
3. Open **ai-security-orchestrator** (or Engineer / Red Team / SOC) → Playground.  
   Prompt (do not use attack / exploit / hijack — the portal filter will show **not allowed**):

   `Assess the authorized healthcare demo. Call runLifecycle with retest true. Summarize finding counts and whether retest_blocked is true.`

Those agents call the Container App through the `foundry-runtime` connection. You do not need `live_test_agents.py` running for Playground.

## 5. Optional: local loop without Foundry agents

Does not invoke the three Azure agents; still exercises the same tools:

```bash
python3 tests/mvp_lifecycle.py
```

## Troubleshooting

| Symptom | What to do |
|---|---|
| `Missing AI_SECURITY_ENGINEER_ID` | Run `python3 infrastructure/deploy_agents.py` |
| `Azure OpenAI not configured` | Put endpoint and key in `.env` |
| Lots of HTTP logs | Prefix the command with `AZURE_LOG_LEVEL=warning` |
| Portal Agents list empty | See `docs/foundry-portal.md` — open the **project**, not the OpenAI resource |
| Red Team errors on missing findings | Run the Engineer step first (the live test script already does this in order) |
