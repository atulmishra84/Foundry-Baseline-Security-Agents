# Architecture: AI Security Agent Platform

Controlled demo on Azure AI Foundry. Red Team may only hit the authorized local `HealthcareAIAssistant` (`tests/vulnerable-app/app.py` and the hardened copy).

## Runtime paths

1. **Local tools** write JSON under `output/` (and A2A messages to `output/a2a-messages.json`).
2. **Azure Container App** `ca-ai-security-runtime` runs the same loop: `POST /v1/lifecycle` (Bearer token) persists to blob `runtime-output` and hosts `GET /dashboard`.
3. **Azure OpenAI** optionally enriches notes when the endpoint is set (Entra ID preferred).
4. **Foundry project agents** call the Container App through OpenAPI plus a **CustomKeys** connection (`foundry-runtime`) that injects `Authorization: Bearer …`. Playground can run `runLifecycle`. The token is not in the prompt.

## Agents

- Security Engineer: `discovery.py` → `assessor.py` → `remediator.py`
- Red Team: `attacker.py` validates T-001 on the allowlisted demo only
- Runtime SOC: `monitor.py` raises incidents; containment is approval-only and not wired to Azure APIs
- Retest: `retest.py` applies CTRL-001/003/005 on `hardened_app.py` and expects `BLOCKED`

## Source of Truth

Threats T-001–T-010 map to OWASP LLM Top 10 2025, MITRE ATLAS, and NIST AI RMF (`sot/frameworks/`). Controls CTRL-001–CTRL-007 sit in `sot/controls/`.

## Design principles

1. Security-first  
2. Least privilege  
3. Evidence before conclusion  
4. Human approval for destructive actions  
5. Common Source of Truth  
6. Deterministic tools around probabilistic reasoning  
7. Everything important must be traceable

## Enterprise (hybrid)

See `docs/ENTERPRISE.md`. Private endpoints sit on `vnet-ai-security` while public access stays enabled. SOC may disable only the allowlisted demo service principal. Power BI and Security Copilot publish are separate tenant steps.  
