#!/usr/bin/env bash

set -euo pipefail

REGION="${REGION:-europe-west9}"
SERVICE_NAME="${SERVICE_NAME:-fx-rate}"
SECRET_NAME="${SECRET_NAME:-EXTERNAL_API_KEY}"

echo "Deploying ${SERVICE_NAME} V3 with Secret Manager..."

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
SERVICE_VERSION=v3,\
REQUEST_TIMEOUT_SECONDS=3,\
DEFAULT_BASE_CURRENCY=USD,\
EXTERNAL_API_BASE_URL=https://api.frankfurter.app/latest \
  --set-secrets \
EXTERNAL_API_KEY="${SECRET_NAME}:latest"

echo "V3 deployment completed."
