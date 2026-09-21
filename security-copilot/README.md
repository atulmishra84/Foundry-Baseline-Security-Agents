# Microsoft Security Copilot agents

These YAML manifests define the same three Foundary agents for [Security Copilot Build](https://securitycopilot.microsoft.com/build).

Microsoft documents YAML upload here: [Build agents by uploading a YAML](https://learn.microsoft.com/en-us/copilot/security/developer/build-agent-yaml-file) and the [agent manifest schema](https://learn.microsoft.com/en-us/copilot/security/developer/agent-manifest).

This repo cannot log into your Security Copilot tenant. Validate locally, then upload in the portal you administer.

```bash
python3 security-copilot/validate_manifests.py
open https://securitycopilot.microsoft.com/build
```

## Files

| Agent | File |
|---|---|
| AI Security Engineer | `security-copilot/ai-security-engineer.yaml` |
| AI Red Team | `security-copilot/ai-red-team.yaml` |
| AI Runtime SOC | `security-copilot/ai-runtime-soc.yaml` |

## Upload steps

1. Open [https://securitycopilot.microsoft.com/build](https://securitycopilot.microsoft.com/build) with a Security Copilot workspace you can author in.
2. Choose **Upload a YAML manifest**.
3. Upload `ai-security-engineer.yaml`. Review tools, then **Publish** / **Create** (wording varies).
4. Repeat for `ai-red-team.yaml` and `ai-runtime-soc.yaml`.
5. Open each agent and run the starter prompt.

Red Team in Security Copilot **does not execute attacks**. It only drafts authorized evidence records. Live validation of the local demo remains `python3 infrastructure/live_test_agents.py` in Foundry.

## After publish

You should see three custom agents in Build. If upload fails on `PromptSkill` or `InteractiveAgent`, switch **View code**, keep Descriptor + SkillGroups, and use the form to set the agent as interactive with the entrypoint skill selected.
