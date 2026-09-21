#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────
# AI Security Agent Platform – Azure Deployment
# ─────────────────────────────────────────────

RESOURCE_GROUP="rg-ai-security-platform"
LOCATION="eastus"
DEPLOYMENT_NAME="ai-security-platform-$(date +%Y%m%d%H%M%S)"

echo "========================================"
echo " AI Security Agent Platform - Deploy"
echo "========================================"
echo "Resource Group : $RESOURCE_GROUP"
echo "Location       : $LOCATION"
echo ""

# Step 1: Create Resource Group
echo "[1/5] Creating resource group '$RESOURCE_GROUP'..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# Step 2: Validate Bicep template
echo ""
echo "[2/5] Validating Bicep template..."
az deployment group validate \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "infrastructure/bicep/main.bicep" \
  --parameters "infrastructure/bicep/main.bicepparam" \
  --output table

# Step 3: Deploy Bicep template
echo ""
echo "[3/5] Deploying Azure AI Foundry resources (this may take 5-10 minutes)..."
DEPLOY_OUTPUT=$(az deployment group create \
  --name "$DEPLOYMENT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "infrastructure/bicep/main.bicep" \
  --parameters "infrastructure/bicep/main.bicepparam" \
  --output json)

echo "$DEPLOY_OUTPUT" > output/azure_deployment_output.json
echo "Deployment output saved to output/azure_deployment_output.json"

# Parse key outputs
STORAGE_ACCOUNT=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['storageAccountName']['value'])")
OPENAI_NAME=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['openAIName']['value'])")
OPENAI_ENDPOINT=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['openAIEndpoint']['value'])")
KEY_VAULT=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['keyVaultName']['value'])")
AI_HUB=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['aiHubName']['value'])")
AI_PROJECT=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['aiProjectName']['value'])")
APP_INSIGHTS_CS=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json; o=json.load(sys.stdin)['properties']['outputs']; print(o['appInsightsConnectionString']['value'])")

echo ""
echo "[4/5] Uploading Source of Truth and schemas to Azure Blob Storage..."
az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --destination source-of-truth \
  --source sot/ \
  --pattern "**/*.json" \
  --overwrite true \
  --output table

az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --destination schemas \
  --source schemas/ \
  --pattern "**/*.json" \
  --overwrite true \
  --output table

# Step 5: Store OpenAI key in Key Vault
echo ""
echo "[5/5] Storing OpenAI API key in Key Vault '$KEY_VAULT'..."
OPENAI_KEY=$(az cognitiveservices account keys list \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "key1" -o tsv)

az keyvault secret set \
  --vault-name "$KEY_VAULT" \
  --name "openai-api-key" \
  --value "$OPENAI_KEY" \
  --output table

# ─────────────────────────────────────────────
echo ""
echo "========================================"
echo "  DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "Azure AI Foundry Hub      : $AI_HUB"
echo "Azure AI Foundry Project  : $AI_PROJECT"
echo "Azure OpenAI Endpoint     : $OPENAI_ENDPOINT"
echo "Storage Account           : $STORAGE_ACCOUNT"
echo "Key Vault                 : $KEY_VAULT"
echo ""
echo "Next: Open the Azure AI Foundry portal:"
echo "  https://ai.azure.com"
echo ""

# Write a .env file for local agent development
cat > .env <<EOF
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_KEY_VAULT_NAME=$KEY_VAULT
AZURE_STORAGE_ACCOUNT=$STORAGE_ACCOUNT
APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS
AZURE_AI_PROJECT=$AI_PROJECT
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
EOF

echo ".env file written for local development."
