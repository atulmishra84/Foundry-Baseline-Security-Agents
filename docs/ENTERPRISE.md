# Enterprise controls (hybrid)

These four tracks are wired in the repo. **Public access stays on** until you explicitly cut over. Do not disable public endpoints until VPN, Bastion, or a jump box can reach the private DNS zones.

## 1. Private VNet / private endpoints

Creates `vnet-ai-security` (10.60.0.0/16) with:

- `snet-private-endpoints` — blob, Key Vault, Azure OpenAI private endpoints
- `snet-container-apps` — reserved for later Container Apps VNet integration
- Private DNS: `privatelink.blob.core.windows.net`, `privatelink.vaultcore.azure.net`, `privatelink.openai.azure.com`

```bash
bash infrastructure/deploy_private_network.sh
```

Hub/project private link and `publicNetworkAccess: Disabled` are **not** applied automatically. That cutover locks operators out of the public portal path. See [Foundry private networking](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link).

## 2. Entra containment APIs

SOC containment disables **one allowlisted demo service principal** (`foundary-demo-healthcare-tool`) via Microsoft Graph. It will not disable users or arbitrary apps.

```bash
bash infrastructure/setup_entra_containment.sh
# After an incident exists:
mkdir -p output/approvals
# copy a real INC-*.json name from output/incident.json
export FOUNDRY_SOC_EXECUTE=true
python3 -c "from tools.runtime.monitor import analyze_evidence; print(analyze_evidence('output/evidence.json'))"
```

Re-enable the demo SP:

```bash
source .env
az ad sp update --id "$FOUNDRY_CONTAINMENT_SP_ID" --set accountEnabled=true
```

The operator (or the Container App MI later) needs Graph permission to update **that** service principal (`Application.ReadWrite.OwnedBy` if you created it, or Application.ReadWrite.All).

## 3. Published Power BI workspace

```bash
python3 tools/dashboard/publish_powerbi.py
```

Creates workspace **Foundary AI Security**, push dataset **FoundaryRiskFindings**, loads `output/powerbi-risk-dataset.csv`. Requires a Power BI / Fabric license that can create workspaces.

## 4. Security Copilot in the tenant

There is no public API to publish custom agents. Validate, then upload in the tenant you administer:

```bash
python3 security-copilot/validate_manifests.py
open https://securitycopilot.microsoft.com/build
```

Upload `security-copilot/ai-security-engineer.yaml`, `ai-red-team.yaml`, `ai-runtime-soc.yaml`, then Publish. Red Team YAML still forbids inventing exploits.
