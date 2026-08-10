#!/usr/bin/env bash

set -euo pipefail

SECRET_NAME="${SECRET_NAME:-EXTERNAL_API_KEY}"

PROJECT_ID="$(
  gcloud config get-value project
)"

PROJECT_NUMBER="$(
  gcloud projects describe "${PROJECT_ID}" \
    --format="value(projectNumber)"
)"

RUNTIME_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Project: ${PROJECT_ID}"
echo "Runtime service account: ${RUNTIME_SERVICE_ACCOUNT}"

gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --member="serviceAccount:${RUNTIME_SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

echo "Secret access granted."
