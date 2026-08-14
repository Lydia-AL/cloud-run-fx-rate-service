#!/usr/bin/env bash

set -euo pipefail

REGION="${REGION:-europe-west9}"
SERVICE_NAME="${SERVICE_NAME:-fx-rate}"

FUNCTION_URL="$(
  gcloud functions describe "${SERVICE_NAME}" \
    --gen2 \
    --region="${REGION}" \
    --format="value(serviceConfig.uri)"
)"

echo "Function URL: ${FUNCTION_URL}"
echo

echo "1. Valid request"
curl --fail-with-body \
  "${FUNCTION_URL}?base=USD&target=EUR"

echo
echo
echo "2. Validation error"
curl --silent \
  --show-error \
  "${FUNCTION_URL}?base=US&target=EU"

echo
