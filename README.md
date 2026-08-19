# Service de taux de change avec Cloud Run Functions

Service serverless de taux de change développé avec Google Cloud Run Functions, Secret Manager, IAM et des logs structurés.

Le projet met en œuvre une stratégie de déploiement progressive :

```text
V1 : réponse simulée (mock)
        |
        v
V2 : API externe réelle
        |
        v
V3 : API réelle avec Secret Manager
        |
        v
V4 : timeout forcé pour tester l'observabilité
```

## Cas d'usage métier

Un pipeline de données dans le retail ou le secteur financier peut ingérer des transactions exprimées dans plusieurs devises.

Plutôt que d'ajouter les taux de change ultérieurement à l'aide de jointures historiques complexes, une fonction serverless peut enrichir chaque transaction avec le taux de change courant au moment de l'ingestion.

Exemple de requête :

```text
GET /?base=USD&target=EUR
```

Exemple de réponse :

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
Client ou pipeline de données
          |
          | Requête HTTP
          v
Cloud Run Function
          |
          +---- Mode mock
          |       |
          |       +--> Taux de change simulé
          |
          +---- Mode live
                  |
                  +--> API externe de taux de change
                  |
                  +--> Secret Manager
                         |
                         +--> EXTERNAL_API_KEY

Cloud Run Function
          |
          +--> Logs JSON structurés
                    |
                    v
              Cloud Logging
```

## Structure du projet

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

## Technologies utilisées

- Google Cloud Run Functions Gen2
- Google Cloud CLI
- Secret Manager
- IAM
- Cloud Logging
- Python 3.11
- Flask
- Requests
- Bash
- API de taux de change Frankfurter

## Stratégie de déploiement

### V1 — Mode mock

La première version renvoie un taux de change simulé de manière déterministe.

```text
MOCK_MODE=true
SERVICE_VERSION=v1
```

Cette version permet de valider :

- le packaging du code source ;
- le déploiement de la Cloud Function ;
- l'appel HTTP ;
- les paramètres de requête ;
- les réponses JSON ;
- les variables d'environnement ;
- les logs structurés.

Elle ne dépend d'aucun service externe.

```bash
bash scripts/deploy_v1_mock.sh
```

### V2 — Mode live

La deuxième version interroge l'API externe de taux de change.

```text
MOCK_MODE=false
SERVICE_VERSION=v2
```

Elle permet de valider :

- les requêtes HTTP sortantes ;
- les réponses de l'API externe ;
- le parsing des réponses ;
- la mesure de la latence ;
- la gestion des timeouts ;
- la gestion des erreurs provenant du service externe.

```bash
bash scripts/deploy_v2_live.sh
```

### V3 — Intégration de Secret Manager

La troisième version injecte `EXTERNAL_API_KEY` depuis Secret Manager.

L'API Frankfurter ne nécessite pas de clé. Le secret est utilisé ici afin de reproduire la configuration qui serait nécessaire avec une API privée ou une API partenaire.

Création du secret :

```bash
EXTERNAL_API_KEY_VALUE="DUMMY_OR_REAL_KEY" \
bash scripts/create_secret.sh
```

Attribution au compte de service d'exécution de l'autorisation d'accéder au secret :

```bash
bash scripts/grant_secret_access.sh
```

Déploiement de la V3 :

```bash
bash scripts/deploy_v3_secret.sh
```

Le secret n'est jamais :

- écrit dans `main.py` ;
- enregistré dans Git ;
- inclus directement dans le script de déploiement.

### V4 — Simulation d'un timeout

La quatrième version configure volontairement un timeout HTTP très court :

```text
REQUEST_TIMEOUT_SECONDS=0.001
```

Cela permet de provoquer :

```text
HTTP 504
event="upstream_timeout"
```

```bash
bash scripts/deploy_v4_timeout_test.sh
```

La V4 est destinée à tester l'observabilité et ne doit pas rester la configuration normale du service.

## Configuration

| Variable d'environnement | Valeur par défaut | Description |
|---|---:|---|
| `MOCK_MODE` | `true` | Active les taux de change simulés |
| `SERVICE_VERSION` | `v1` | Version logique de l'application |
| `REQUEST_TIMEOUT_SECONDS` | `3` | Timeout de la requête vers le service externe |
| `DEFAULT_BASE_CURRENCY` | `USD` | Devise source par défaut |
| `EXTERNAL_API_BASE_URL` | URL Frankfurter | Endpoint de l'API externe |
| `EXTERNAL_API_KEY` | Aucune | Secret injecté par Secret Manager |

## Réponses HTTP

| Statut | Signification | Événement applicatif |
|---:|---|---|
| `200` | Taux renvoyé avec succès | `rate_mock` ou `rate_ok` |
| `400` | Code de devise invalide | `validation_error` |
| `500` | Erreur interne inattendue | `unexpected_error` |
| `502` | Échec de l'API externe | `auth_failed_upstream`, `upstream_http_error` ou `unexpected_payload` |
| `504` | Timeout de l'API externe | `upstream_timeout` |

## Logs structurés

La fonction écrit des logs JSON sur la sortie standard.

Exemple :

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

Cela permet d'effectuer des recherches précises dans Logs Explorer, par exemple :

```text
resource.type="cloud_run_revision"
resource.labels.service_name="fx-rate"
jsonPayload.event="rate_ok"
```

Consultez `docs/logging.md` pour davantage d'exemples.

## IAM et principe du moindre privilège

La fonction s'exécute avec un compte de service.

Ce compte de service doit recevoir explicitement l'autorisation de lire le secret :

```text
roles/secretmanager.secretAccessor
```

Le rôle est attribué directement sur `EXTERNAL_API_KEY`, plutôt que sur l'ensemble des secrets du projet.

Cette configuration respecte le principe du moindre privilège : le service reçoit uniquement les autorisations nécessaires à son exécution.

## Tests

Récupération de l'URL du service et envoi de requêtes de test :

```bash
bash scripts/test_function.sh
```

Requête valide :

```bash
curl "${FUNCTION_URL}?base=USD&target=EUR"
```

Erreur de validation :

```bash
curl "${FUNCTION_URL}?base=US&target=EU"
```

## Bonnes pratiques de sécurité

- Ne jamais enregistrer de clés API ou d'identifiants de comptes de service dans Git.
- Privilégier des comptes de service d'exécution dédiés dans un environnement de production.
- Attribuer les permissions IAM au niveau de ressource le plus précis possible.
- Éviter les appels publics lorsque ceux-ci ne sont pas nécessaires.
- Dans les systèmes de production sensibles, utiliser une version précise d'un secret plutôt que systématiquement `latest`.
- Ne jamais inclure la valeur des secrets dans les logs ou les réponses d'erreur.

## Limites

Ce projet est réalisé dans un objectif pédagogique.

- L'API Frankfurter est publique et ne nécessite aucune authentification.
- La clé API est utilisée uniquement pour démontrer l'intégration de Secret Manager.
- Aucune couche de persistance n'est utilisée.
- Aucun API Gateway ni mécanisme de limitation du nombre de requêtes n'est configuré.
- L'authentification est désactivée pour les besoins de la démonstration.
- Les scripts de déploiement utilisent le compte de service Compute Engine par défaut.

Une évolution destinée à un environnement de production pourrait intégrer :

- un compte de service d'exécution dédié ;
- des appels authentifiés ;
- API Gateway ;
- le tracing des requêtes et des identifiants de corrélation ;
- des tests unitaires et d'intégration ;
- des stratégies de retry avec backoff exponentiel ;
- des dashboards de monitoring et des alertes ;
- un déploiement continu avec GitHub Actions ou Cloud Build.

## Compétences mises en œuvre

- développement serverless en Python ;
- déploiement de Cloud Run Functions ;
- utilisation de Google Cloud CLI ;
- intégration d'une API externe ;
- configuration par variables d'environnement ;
- Secret Manager ;
- IAM et comptes de service ;
- principe du moindre privilège ;
- logs structurés ;
- requêtes dans Logs Explorer ;
- gestion des erreurs HTTP ;
- simulation de timeouts ;
- versioning des déploiements et révisions Cloud Run.
