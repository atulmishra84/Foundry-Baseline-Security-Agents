# Threat Model

## Boundaries

- **In scope:** local healthcare demo agent, SoT, Foundry-hosted reasoning, A2A artifacts.
- **Out of scope:** attacking third-party or production systems.

## Mapped threats (OWASP LLM Top 10 2025)

| ID | Threat | Typical evidence in this repo |
|---|---|---|
| LLM01 / T-001 | Prompt injection | Unvalidated `process_prompt` |
| LLM02 / T-002 | Sensitive disclosure | `patient_search` bulk return |
| LLM03 / T-003 | Supply chain | Empty dependency inventory |
| LLM04 / T-004 | Poisoning | N/A without a vector store |
| LLM05 / T-005 | Improper output handling | Raw tool output to caller |
| LLM06 / T-006 | Excessive agency | `system-admin-identity` |
| LLM07 / T-007 | System prompt leakage | No prompt isolation control |
| LLM08 / T-008 | Vector weaknesses | N/A without embeddings |
| LLM09 / T-009 | Misinformation | No grounding control |
| LLM10 / T-010 | Unbounded consumption | No rate limit on the agent |

## Platform self-threats

- Secrets in `.env` and Azure deployment output must stay uncommitted.
- Red Team may only run against the authorized local demo.
