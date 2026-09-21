# Run on the Azure AI Foundry ecosystem

Goal: Engineer, Red Team, SOC, artifacts, and SoT live next to the Foundry hub—not only on a laptop.

## What runs where

| Piece | Where |
|---|---|
| `ai-security-engineer`, `ai-red-team`, `ai-runtime-soc` | Foundry project agents |
| `ai-security-orchestrator` | Foundry agent that **connects** the three (in-project A2A) |
| Closed-loop tools + demo app | Container App `ca-ai-security-runtime` in `rg-ai-security-platform` |
| JSON artifacts | Hub storage `runtime-output` + local `output/` |
| SoT / schemas | Blob containers `source-of-truth`, `schemas` |
| Traces | Application Insights `ai-security-insights` |

## Deploy / update

```bash
cd /Users/mac/Foundary
python3 infrastructure/deploy_agents.py
python3 infrastructure/foundry_orchestrator.py
bash infrastructure/sync_sot.sh
bash infrastructure/deploy_foundry_runtime.sh
```

Then:

```bash
curl -sS https://ca-ai-security-runtime.wonderfulriver-296ea5d0.eastus.azurecontainerapps.io/health
source .env
curl -sS -H "Authorization: Bearer $FOUNDRY_RUNTIME_TOKEN" \
  -X POST 'https://ca-ai-security-runtime.wonderfulriver-296ea5d0.eastus.azurecontainerapps.io/v1/lifecycle?retest=true'
curl -sS -H "Authorization: Bearer $FOUNDRY_RUNTIME_TOKEN" \
  https://ca-ai-security-runtime.wonderfulriver-296ea5d0.eastus.azurecontainerapps.io/dashboard -o /tmp/dashboard.html
curl -sS -H "Authorization: Bearer $FOUNDRY_RUNTIME_TOKEN" \
  https://ca-ai-security-runtime.wonderfulriver-296ea5d0.eastus.azurecontainerapps.io/v1/artifacts
open /tmp/dashboard.html
```

In Foundry, open **ai-security-orchestrator** and ask it to run Engineer → Red Team → SOC on the authorized healthcare demo only.

The container identity needs **Storage Blob Data Contributor** on the storage account and **Cognitive Services OpenAI User** on the OpenAI resource. Assign those if blob/OpenAI calls fail from the app.
