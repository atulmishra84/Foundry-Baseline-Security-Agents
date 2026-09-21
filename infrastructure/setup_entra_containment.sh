#!/usr/bin/env bash
set -euo pipefail
# Create the allowlisted demo SP used by SOC containment. Does not disable it.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${FOUNDRY_CONTAINMENT_APP_NAME:-foundary-demo-healthcare-tool}"

APP_ID=$(az ad app list --display-name "$NAME" --query "[0].appId" -o tsv)
if [[ -z "$APP_ID" ]]; then
  APP_ID=$(az ad app create --display-name "$NAME" --sign-in-audience AzureADMyOrg --query appId -o tsv)
  echo "Created app $NAME $APP_ID"
else
  echo "App already exists $APP_ID"
fi

SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
if [[ -z "$SP_ID" ]]; then
  SP_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)
  echo "Created service principal $SP_ID"
else
  echo "Service principal already exists $SP_ID"
fi

ENV="$ROOT/.env"
touch "$ENV"
grep -v '^FOUNDRY_CONTAINMENT_SP_ID=' "$ENV" >"$ENV.tmp" || true
echo "FOUNDRY_CONTAINMENT_SP_ID=$SP_ID" >>"$ENV.tmp"
mv "$ENV.tmp" "$ENV"
echo "Wrote FOUNDRY_CONTAINMENT_SP_ID to .env"
az ad sp show --id "$SP_ID" --query "{id:id,appId:appId,accountEnabled:accountEnabled,displayName:displayName}" -o json
