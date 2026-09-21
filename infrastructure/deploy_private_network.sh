#!/usr/bin/env bash
set -euo pipefail
# Hybrid private endpoints. Does NOT disable public access (demo stays reachable).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RG="${AZURE_RESOURCE_GROUP:-rg-ai-security-platform}"
LOC="${AZURE_LOCATION:-eastus}"
STORAGE="${AZURE_STORAGE_ACCOUNT:-staiseclfje77wuun}"
KV="${AZURE_KEY_VAULT_NAME:-kv-sec-lfje77wuun}"
AOAI="${AZURE_OPENAI_ACCOUNT:-aoai-ai-security-lfje77wuunkb4}"

az provider register --namespace Microsoft.Network --wait >/dev/null
echo "What-if private network..."
az deployment group what-if \
  --resource-group "$RG" \
  --template-file "$ROOT/infrastructure/bicep/private-network.bicep" \
  --parameters location="$LOC" storageAccountName="$STORAGE" keyVaultName="$KV" openAiAccountName="$AOAI"

echo "Deploying VNet + private endpoints (public access stays Enabled)..."
az deployment group create \
  --resource-group "$RG" \
  --name foundary-private-network \
  --template-file "$ROOT/infrastructure/bicep/private-network.bicep" \
  --parameters location="$LOC" storageAccountName="$STORAGE" keyVaultName="$KV" openAiAccountName="$AOAI" \
  --output table

echo "Private endpoints:"
az network private-endpoint list -g "$RG" --query "[].{name:name,provisioning:provisioningState}" -o table
echo "Public access is still Enabled. Cutover (Disable) is a separate, explicit change — see docs/ENTERPRISE.md."
