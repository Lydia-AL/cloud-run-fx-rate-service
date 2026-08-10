#!/usr/bin/env bash

set -euo pipefail

REGION="${REGION:-europe-west9}"
SERVICE_NAME="${SERVICE_NAME:-fx-rate}"

echo "Deploying ${SERVICE_NAME} V2 in live mode..."

gcloud functions deploy "${SERVICE_NAME}" \
  --gen2 \
  --region="${REGION}" \
  --runtime=python311 \
  --source=. \
  --entry-point=fx_rate \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars \
MOCK_MODE=false,\
LOG_LEVEL=INFO,\
SERVICE_VERSION=v2,\
REQUEST_TIMEOUT_SECONDS=3,\
DEFAULT_BASE_CURRENCY=USD,\
EXTERNAL_API_BASE_URL=https://api.frankfurter.app/latest

echo "V2 deployment completed."
