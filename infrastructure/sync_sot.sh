#!/usr/bin/env bash
set -euo pipefail
ACCOUNT="${AZURE_STORAGE_ACCOUNT:-staiseclfje77wuun}"
echo "Uploading SoT and schemas to $ACCOUNT"
az storage blob upload-batch \
  --account-name "$ACCOUNT" \
  --auth-mode login \
  --destination source-of-truth \
  --source sot/ \
  --pattern "**/*.json" \
  --overwrite true \
  --output table
az storage blob upload-batch \
  --account-name "$ACCOUNT" \
  --auth-mode login \
  --destination schemas \
  --source schemas/ \
  --pattern "**/*.json" \
  --overwrite true \
  --output table
echo "SoT sync complete."
