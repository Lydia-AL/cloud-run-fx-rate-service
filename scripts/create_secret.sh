#!/usr/bin/env bash

set -euo pipefail

SECRET_NAME="${SECRET_NAME:-EXTERNAL_API_KEY}"

if [[ -z "${EXTERNAL_API_KEY_VALUE:-}" ]]; then
  echo "Missing EXTERNAL_API_KEY_VALUE."
  echo
  echo "Run the script with:"
  echo "EXTERNAL_API_KEY_VALUE='your-key' bash scripts/create_secret.sh"
  exit 1
fi

if gcloud secrets describe "${SECRET_NAME}" >/dev/null 2>&1; then
  echo "Secret ${SECRET_NAME} already exists."
else
  echo "Creating secret ${SECRET_NAME}..."

  gcloud secrets create "${SECRET_NAME}" \
    --replication-policy=automatic
fi

echo "Adding a new secret version..."

printf '%s' "${EXTERNAL_API_KEY_VALUE}" |
  gcloud secrets versions add "${SECRET_NAME}" \
    --data-file=-

echo "Secret version created."
