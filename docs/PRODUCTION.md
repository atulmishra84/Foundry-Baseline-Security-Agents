# Production readiness

This platform is **production-hardened for a controlled demo**, not a multi-tenant SaaS. Do not aim Red Team or SOC containment at customer systems.

## What is now in place

| Control | Behavior |
|---|---|
| Target allowlist | `config/production.json` — vulnerable demo + hardened copy only |
| PHI redaction | Evidence stores `[REDACTED]` + record ids, not clinical fields |
| SOC containment | Off unless `output/approvals/{incident_id}.json` exists **and** `FOUNDRY_SOC_EXECUTE=true` |
| OpenAI auth | Entra ID by default (`FOUNDRY_USE_AZURE_AD=true`). Set to `false` to use a key |
| SoT sync | `bash infrastructure/sync_sot.sh` — OWASP, MITRE ATLAS, NIST AI RMF |
| Apply + retest | `tools/security/retest.py` re-runs T-001 on `hardened_app.py` and expects `BLOCKED` |
| Runtime API | Container App `POST /v1/lifecycle?retest=true` and `GET /dashboard` |
| Runtime token | If `FOUNDRY_RUNTIME_TOKEN` is set, lifecycle requires `Authorization: Bearer …` |
| Orchestrator | Foundry agent can call the runtime OpenAPI spec plus the three child agents |

## Go-live checklist (human)

1. Rotate the Azure OpenAI key if it was ever pasted into chat, git, or tickets.
2. Assign **Cognitive Services OpenAI User** on `aoai-ai-security-*` to the operator and the project managed identity.
3. Run `bash infrastructure/sync_sot.sh`.
4. Confirm `.env` and `output/` stay gitignored.
5. Review public network access on the hub and OpenAI account; private endpoints are still a separate change.
6. Set `FOUNDRY_RUNTIME_TOKEN` on the Container App and restrict ingress if this leaves a lab.
7. Hybrid private endpoints: `bash infrastructure/deploy_private_network.sh` (do not disable public access yet).
8. Entra demo SP: `bash infrastructure/setup_entra_containment.sh`
9. Power BI workspace: `python3 tools/dashboard/publish_powerbi.py` (needs a Fabric/Power BI license).
10. Security Copilot: `python3 security-copilot/validate_manifests.py` then upload at https://securitycopilot.microsoft.com/build
8. Host `infrastructure/live_test_agents.py` as a locked runner if portal Playground must call Function tools.

## Run after hardening

```bash
export FOUNDRY_USE_AZURE_AD=true
python3 -m unittest tests.test_schemas tests.test_production_controls tests.test_retest
python3 tests/mvp_lifecycle.py
AZURE_LOG_LEVEL=warning python3 infrastructure/live_test_agents.py
python3 infrastructure/foundry_orchestrator.py
```

Dashboard after a lifecycle: `output/executive-dashboard.html` or `GET /dashboard` on the runtime.

## Approval file example

`output/approvals/INC-xxxxxxxx.json`:

```json
{
  "approved_by": "security.oncall@example.com",
  "action": "disable_patient_search_tool",
  "ticket": "INC-123"
}
```

Containment still does **not** call Azure APIs. Approval only records intent until you wire Entra disable / tool flags.
