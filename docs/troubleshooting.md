# Troubleshooting

## `iam.serviceaccounts.actAs` denied

Example:

```text
Permission 'iam.serviceaccounts.actAs' denied on service account
PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

The deploying identity is not allowed to act as the runtime service
account.

```bash
PROJECT_ID=$(gcloud config get-value project)

PROJECT_NUMBER=$(
  gcloud projects describe "${PROJECT_ID}" \
    --format="value(projectNumber)"
)

RUNTIME_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

DEPLOYER=$(gcloud config get-value account)

gcloud iam service-accounts add-iam-policy-binding \
  "${RUNTIME_SERVICE_ACCOUNT}" \
  --member="user:${DEPLOYER}" \
  --role="roles/iam.serviceAccountUser"
```

## Permission denied on Secret Manager

Example:

```text
Permission denied on secret EXTERNAL_API_KEY.

The service account used must be granted the Secret Manager Secret
Accessor role.
```

The message identifies:

- the secret;
- the runtime service account;
- the missing IAM role.

Fix:

```bash
bash scripts/grant_secret_access.sh
```

The assigned role is:

```text
roles/secretmanager.secretAccessor
```

## HTTP 403 when opening the function

If the service is deployed but the browser returns:

```text
The request was not authenticated.
```

Verify the Cloud Run IAM policy:

```bash
gcloud run services get-iam-policy fx-rate \
  --region=europe-west9
```

A public demonstration service should contain:

```text
allUsers
roles/run.invoker
```

If required:

```bash
gcloud run services add-iam-policy-binding fx-rate \
  --region=europe-west9 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

Do not expose a production service publicly unless this is explicitly
required by the architecture.

## Region variable is empty

Check:

```bash
echo "${REGION:-}"
```

Set it:

```bash
export REGION=europe-west9
```

Or configure a default:

```bash
gcloud config set functions/region europe-west9
```

## Bash reports `--region: command not found`

The multiline command was broken.

The backslash must be the final character on the line:

```bash
gcloud functions deploy fx-rate \
  --gen2 \
  --region=europe-west9
```

There must be no space after `\`.

Do not copy the terminal prompt:

```text
user@cloudshell:~ (project-id)$
```

Only copy the command written after `$`.
