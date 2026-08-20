# Logs structurés

La fonction génère des logs au format JSON sur la sortie standard.

Cloud Run collecte automatiquement ces logs et les envoie vers Cloud Logging.

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

## Logs HTTP et logs applicatifs

Cloud Run génère automatiquement des logs de requêtes contenant des informations telles que :

- la méthode HTTP ;
- l'URL de la requête ;
- le code de statut ;
- la latence ;
- le user agent.

L'application génère également des logs structurés qui permettent de comprendre pourquoi un statut particulier a été renvoyé.

Par exemple :

```text
HTTP status: 400
Application event: validation_error
```

Le statut HTTP décrit le résultat reçu par le client.

L'événement structuré fournit la raison métier ou technique à l'origine de ce résultat.
