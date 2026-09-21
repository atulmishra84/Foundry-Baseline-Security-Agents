# AI Security Agent Platform on Microsoft Foundry

Three specialized agents share an AI Security Source of Truth and produce auditable JSON.

1. **AI Security Engineer** — discover, assess, remediate  
2. **AI Adversary / Red Team** — validate authorized local findings  
3. **AI Runtime SOC** — detect and raise incidents  

Production-style controls: `docs/PRODUCTION.md`. Hybrid VNet, Entra containment, Power BI, Security Copilot: `docs/ENTERPRISE.md`. This is still a controlled demo, not multi-tenant SaaS.  

## Phases

| Phase | Status |
|---|---|
| 0–5 Foundation, SoT, agents, local orchestration | Complete |
| 6 Live Azure OpenAI (optional; falls back if unset) | Complete |
| 7 CI/CD (GitHub Actions) | Complete |
| 8 OWASP LLM Top 10 SoT + coverage report | Complete |
| 9 A2A message bus | Complete |
| 10 Executive HTML dashboard + Power BI CSV | Complete |
| Production base (allowlist, retest, ATLAS/NIST, runtime API) | Complete |

## Run locally

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env   # add AZURE_OPENAI_* to enable Foundry reasoning
python3 tests/mvp_lifecycle.py
```

Open `output/executive-dashboard.html`. See `docs/power-bi.md` for Power BI.

Without `AZURE_OPENAI_API_KEY`, tools stay deterministic and still write full artifacts.

## Live test Foundry agents

```bash
python3 infrastructure/deploy_agents.py
python3 infrastructure/live_test_agents.py
```

This attaches tools to the three project agents and runs them in Azure. Red Team may only call the authorized local healthcare demo. Results: `output/foundry-live-test.json`.

To view them in the portal, open the **project** `project-security-agents` (not the Azure OpenAI resource). See `docs/foundry-portal.md`.

Security Copilot (separate product): upload the YAML under `security-copilot/` at [https://securitycopilot.microsoft.com/build](https://securitycopilot.microsoft.com/build). Steps in `security-copilot/README.md`.

## Layout

- `agents/` — agent missions  
- `sot/` — threats, attacks, controls, frameworks  
- `schemas/` — JSON contracts including A2A  
- `tools/foundry/` — Azure OpenAI client  
- `tools/a2a/` — agent-to-agent bus  
- `infrastructure/` — Bicep + Foundry agent deploy  
- `.github/workflows/ci.yml` — tests and lifecycle  
