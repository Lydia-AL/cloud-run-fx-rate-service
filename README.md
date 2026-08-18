# Cloud Run FX Rate Service

A serverless foreign-exchange rate service built with Google Cloud Run
Functions, Secret Manager, IAM and structured logging.

The project demonstrates a progressive deployment workflow:

```text
V1: mock response
        |
        v
V2: live external API
        |
        v
V3: live API with Secret Manager
        |
        v
V4: forced timeout for observability testing
```

## Business use case

A retail or financial data pipeline may ingest transactions expressed in
multiple currencies.

Instead of adding exchange rates later through complex historical joins,
a serverless function can enrich each transaction with the current rate
during ingestion.

Example request:

```text
GET /?base=USD&target=EUR
```

Example response:

```json
{
  "base": "USD",
  "mode": "live",
  "rate": 0.87,
  "target": "EUR",
  "version": "v3"
}
```

## Architecture

```text
Client or data pipeline
          |
          | HTTP request
          v
Cloud Run Function
          |
          +---- Mock mode
          |       |
          |       +--> Simulated exchange rate
          |
          +---- Live mode
                  |
                  +--> External FX API
                  |
                  +--> Secret Manager
                         |
                         +--> EXTERNAL_API_KEY

Cloud Run Function
          |
          +--> Structured JSON logs
                    |
                    v
              Cloud Logging
```

## Project structure

```text
.
├── README.md
├── .gitignore
├── main.py
├── requirements.txt
├── scripts/
│   ├── deploy_v1_mock.sh
│   ├── deploy_v2_live.sh
│   ├── create_secret.sh
│   ├── grant_secret_access.sh
│   ├── deploy_v3_secret.sh
│   ├── deploy_v4_timeout_test.sh
│   └── test_function.sh
└── docs/
    ├── logging.md
    └── troubleshooting.md
```

## Technologies

- Google Cloud Run Functions Gen2
- Google Cloud CLI
- Secret Manager
- IAM
- Cloud Logging
- Python 3.11
- Flask
- Requests
- Bash
- Frankfurter foreign-exchange API

## Deployment strategy

### V1 — Mock mode

The first version returns a deterministic simulated rate.

```text
MOCK_MODE=true
SERVICE_VERSION=v1
```

This version validates:

- source packaging;
- Cloud Function deployment;
- HTTP invocation;
- query parameters;
- JSON responses;
- environment variables;
- structured logging.

It does not depend on an external service.

```bash
bash scripts/deploy_v1_mock.sh
```

### V2 — Live mode

The second version calls the external exchange-rate API.

```text
MOCK_MODE=false
SERVICE_VERSION=v2
```

It validates:

- outbound HTTP requests;
- external API responses;
- response parsing;
- latency measurement;
- timeout handling;
- upstream error handling.

```bash
bash scripts/deploy_v2_live.sh
```

### V3 — Secret Manager integration

The third version injects `EXTERNAL_API_KEY` from Secret Manager.

The Frankfurter API does not require a key. The secret is included to
demonstrate how a private or partner API would be configured.

Create the secret:

```bash
EXTERNAL_API_KEY_VALUE="DUMMY_OR_REAL_KEY" \
bash scripts/create_secret.sh
```

Grant the runtime service account access:

```bash
bash scripts/grant_secret_access.sh
```

Deploy V3:

```bash
bash scripts/deploy_v3_secret.sh
```

The secret is never:

- written in `main.py`;
- committed to Git;
- included directly in the deployment script.

### V4 — Timeout simulation

The fourth version sets an intentionally short HTTP timeout:

```text
REQUEST_TIMEOUT_SECONDS=0.001
```

This is used to produce:

```text
HTTP 504
event="upstream_timeout"
```

```bash
bash scripts/deploy_v4_timeout_test.sh
```

V4 is an observability test and should not remain as the normal service
configuration.

## Configuration

| Environment variable | Default | Description |
|---|---:|---|
| `MOCK_MODE` | `true` | Enables simulated exchange rates |
| `SERVICE_VERSION` | `v1` | Logical application version |
| `REQUEST_TIMEOUT_SECONDS` | `3` | External request timeout |
| `DEFAULT_BASE_CURRENCY` | `USD` | Default source currency |
| `EXTERNAL_API_BASE_URL` | Frankfurter URL | External API endpoint |
| `EXTERNAL_API_KEY` | None | Secret injected by Secret Manager |

## HTTP responses

| Status | Meaning | Application event |
|---:|---|---|
| `200` | Rate returned successfully | `rate_mock` or `rate_ok` |
| `400` | Invalid currency code | `validation_error` |
| `500` | Unexpected internal error | `unexpected_error` |
| `502` | External API failure | `auth_failed_upstream`, `upstream_http_error` or `unexpected_payload` |
| `504` | External API timeout | `upstream_timeout` |

## Structured logging

The function writes JSON logs to standard output.

Example:

```json
{
  "severity": "INFO",
  "event": "rate_ok",
  "service_version": "v3",
  "base": "USD",
  "target": "EUR",
  "rate": 0.87,
  "latency_ms": 120
}
```

This allows precise Logs Explorer queries such as:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
jsonPayload.event="rate_ok"
```

See [`docs/logging.md`](docs/logging.md) for more examples.

## IAM and least privilege

The function runs with a service account.

This service account must explicitly receive permission to read the
secret:

```text
roles/secretmanager.secretAccessor
```

The role is granted directly on `EXTERNAL_API_KEY`, rather than on every
secret in the project.

This follows the principle of least privilege: the service receives only
the permissions required for its execution.

## Testing

Retrieve the service URL and send example requests:

```bash
bash scripts/test_function.sh
```

Valid request:

```bash
curl "${FUNCTION_URL}?base=USD&target=EUR"
```

Validation error:

```bash
curl "${FUNCTION_URL}?base=US&target=EU"
```

## Security notes

- Never commit API keys or service-account credentials.
- Prefer dedicated runtime service accounts in production.
- Grant IAM permissions at the narrowest possible resource level.
- Avoid public invocation unless it is required.
- Pin a specific secret version in sensitive production systems instead
  of always using `latest`.
- Do not include secret values in logs or error responses.

## Limitations

This is an educational project.

- The Frankfurter API is public and does not require authentication.
- The API key is included only to demonstrate Secret Manager.
- No persistence layer is used.
- No API gateway or rate limiting is configured.
- Authentication is disabled for demonstration purposes.
- The deployment scripts use the default Compute Engine service account.

A production evolution could include:

- a dedicated runtime service account;
- authenticated invocation;
- API Gateway;
- request tracing and correlation IDs;
- unit and integration tests;
- retry policies with exponential backoff;
- monitoring dashboards and alerting;
- continuous deployment through GitHub Actions or Cloud Build.

## Skills demonstrated

- serverless Python development;
- Cloud Run Functions deployment;
- Google Cloud CLI;
- API integration;
- environment-based configuration;
- Secret Manager;
- IAM and service accounts;
- least-privilege access;
- structured logging;
- Logs Explorer queries;
- HTTP error handling;
- timeout simulation;
- deployment versioning and Cloud Run revisions.

## Context

This project was completed as part of the Cloud Data Engineering
training program on Google Cloud delivered by Data Upskilling.
