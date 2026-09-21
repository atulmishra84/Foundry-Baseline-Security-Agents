#!/usr/bin/env bash
set -euo pipefail
# Build linux/amd64, push ACR, update Container App. az containerapp up --source is unreliable on Apple Silicon.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RG="${AZURE_RESOURCE_GROUP:-rg-ai-security-platform}"
LOC="${AZURE_LOCATION:-eastus}"
APP="ca-ai-security-runtime"
ENV_NAME="cae-ai-security"
ACR="${AZURE_ACR_NAME:-cae819a04a07acr}"
TAG="${FOUNDRY_RUNTIME_IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
IMAGE="${ACR}.azurecr.io/${APP}:${TAG}"
LATEST="${ACR}.azurecr.io/${APP}:latest"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ -z "${FOUNDRY_RUNTIME_TOKEN:-}" ]]; then
  FOUNDRY_RUNTIME_TOKEN="$(openssl rand -hex 24)"
  if grep -q '^FOUNDRY_RUNTIME_TOKEN=' "$ROOT/.env" 2>/dev/null; then
    tmp="$(mktemp)"
    grep -v '^FOUNDRY_RUNTIME_TOKEN=' "$ROOT/.env" >"$tmp"
    echo "FOUNDRY_RUNTIME_TOKEN=${FOUNDRY_RUNTIME_TOKEN}" >>"$tmp"
    mv "$tmp" "$ROOT/.env"
  else
    echo "FOUNDRY_RUNTIME_TOKEN=${FOUNDRY_RUNTIME_TOKEN}" >>"$ROOT/.env"
  fi
  echo "Wrote FOUNDRY_RUNTIME_TOKEN to .env (not printed)."
fi

echo "Ensuring Container Apps environment..."
az provider register --namespace Microsoft.App --wait >/dev/null
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RG" \
  --location "$LOC" \
  --logs-destination none \
  --yes 2>/dev/null || true

echo "Building ${IMAGE} in ACR (linux/amd64, avoids local QEMU/PyPI timeouts)..."
az acr build \
  --registry "$ACR" \
  --image "${APP}:${TAG}" \
  --image "${APP}:latest" \
  --platform linux/amd64 \
  "$ROOT"

echo "Updating Container App..."
az containerapp update \
  --name "$APP" \
  --resource-group "$RG" \
  --image "$IMAGE" \
  --set-env-vars \
    AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}" \
    AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4o}" \
    FOUNDRY_USE_AZURE_AD=true \
    AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-staiseclfje77wuun}" \
    AZURE_RESOURCE_GROUP="$RG" \
    AZURE_AI_PROJECT="${AZURE_AI_PROJECT:-project-security-agents}" \
    FOUNDRY_RUNTIME_TOKEN="$FOUNDRY_RUNTIME_TOKEN" \
    FOUNDRY_SOC_EXECUTE=false \
    FOUNDRY_CONTAINMENT_SP_ID="${FOUNDRY_CONTAINMENT_SP_ID:-}"

FQDN=$(az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
echo "Runtime URL: https://$FQDN/health"
echo "Dashboard:   GET https://$FQDN/dashboard  (Bearer FOUNDRY_RUNTIME_TOKEN)"
echo "Lifecycle:   POST https://$FQDN/v1/lifecycle?retest=true"
