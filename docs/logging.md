# Structured logging

The function emits JSON logs to standard output.

Cloud Run automatically collects these logs and sends them to Cloud
Logging.

## Successful live request

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

## Validation error

```json
{
  "severity": "WARNING",
  "event": "validation_error",
  "service_version": "v3",
  "base": "US",
  "target": "EU"
}
```

## Upstream timeout

```json
{
  "severity": "WARNING",
  "event": "upstream_timeout",
  "service_version": "v4",
  "url": "https://api.frankfurter.app/latest?from=USD&to=EUR",
  "timeout_seconds": 0.001
}
```

## Logs Explorer filters

Only show Cloud Run revision logs:

```text
resource.type="cloud_run_revision"
```

Filter on the service:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
```

Successful live requests:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
jsonPayload.event="rate_ok"
```

Validation errors:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
jsonPayload.event="validation_error"
```

Timeouts:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
jsonPayload.event="upstream_timeout"
```

Errors only:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
severity>=ERROR
```

HTTP 400 requests:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
httpRequest.status=400
```

HTTP 504 requests:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
httpRequest.status=504
```

## HTTP logs and application logs

Cloud Run produces automatic request logs containing information such as:

- HTTP method;
- request URL;
- status code;
- latency;
- user agent.

The application also emits structured logs explaining why a particular
status was returned.

For example:

```text
HTTP status: 400
Application event: validation_error
```

The HTTP status describes the result received by the client.

The structured event provides the business or technical reason behind
that result.
