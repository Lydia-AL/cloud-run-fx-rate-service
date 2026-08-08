"""Cloud Run Function providing foreign-exchange rates.

The function supports two execution modes:

- mock mode: returns a deterministic simulated exchange rate;
- live mode: retrieves the rate from an external HTTP API.

Configuration is provided through environment variables.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import requests
from flask import Request, Response, jsonify


API_BASE = os.getenv(
    "EXTERNAL_API_BASE_URL",
    "https://api.frankfurter.app/latest",
)

DEFAULT_BASE = os.getenv("DEFAULT_BASE_CURRENCY", "USD")

REQUEST_TIMEOUT = float(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "3")
)

SERVICE_VERSION = os.getenv("SERVICE_VERSION", "v1")

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# Injected from Secret Manager during the V3 deployment.
# Frankfurter does not require a key; it is included for demonstration.
API_KEY = os.getenv("EXTERNAL_API_KEY")


def log_event(
    severity: str,
    event: str,
    **fields: Any,
) -> None:
    """Write a structured JSON log to stdout.

    Cloud Run automatically collects stdout and sends it to Cloud Logging.
    JSON fields can then be queried directly from Logs Explorer.
    """

    payload = {
        "severity": severity.upper(),
        "event": event,
        "service_version": SERVICE_VERSION,
        **fields,
    }

    print(json.dumps(payload, default=str), flush=True)


def build_url(base: str, target: str) -> str:
    """Build the external API URL for the requested currencies."""

    host = (urlparse(API_BASE).hostname or "").lower()

    if "frankfurter.app" in host:
        return f"{API_BASE}?from={base}&to={target}"

    return f"{API_BASE}?base={base}&symbols={target}"


def fx_rate(request: Request) -> Response | tuple[Response, int]:
    """Return a simulated or live foreign-exchange rate."""

    started_at = time.perf_counter()

    base = (
        request.args.get("base")
        or DEFAULT_BASE
    ).upper()

    target = (
        request.args.get("target")
        or "EUR"
    ).upper()

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    if len(base) != 3 or len(target) != 3:
        log_event(
            severity="WARNING",
            event="validation_error",
            base=base,
            target=target,
        )

        return (
            jsonify(
                error="Use three-character ISO 4217 codes such as USD or EUR"
            ),
            400,
        )

    # ------------------------------------------------------------------
    # Mock mode
    # ------------------------------------------------------------------

    if MOCK_MODE:
        seed = sum(map(ord, base + target))
        rate_value = round((seed % 200) / 10 + 0.5, 4)

        latency_ms = int(
            (time.perf_counter() - started_at) * 1000
        )

        log_event(
            severity="INFO",
            event="rate_mock",
            base=base,
            target=target,
            rate=rate_value,
            latency_ms=latency_ms,
        )

        return jsonify(
            version=SERVICE_VERSION,
            mode="mock",
            base=base,
            target=target,
            rate=rate_value,
        )

    # ------------------------------------------------------------------
    # Live mode
    # ------------------------------------------------------------------

    url = build_url(base, target)

    headers = (
        {"Authorization": f"Bearer {API_KEY}"}
        if API_KEY
        else {}
    )

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 401:
            log_event(
                severity="ERROR",
                event="auth_failed_upstream",
                status=response.status_code,
                url=url,
            )

            return jsonify(error="Upstream authentication failed"), 502

        response.raise_for_status()

        data = response.json()

        rate_value = None

        if (
            isinstance(data, dict)
            and isinstance(data.get("rates"), dict)
            and target in data["rates"]
        ):
            rate_value = float(data["rates"][target])

        if rate_value is None:
            log_event(
                severity="ERROR",
                event="unexpected_payload",
                payload_sample=str(data)[:300],
            )

            return jsonify(error="Unexpected upstream payload"), 502

        latency_ms = int(
            (time.perf_counter() - started_at) * 1000
        )

        log_event(
            severity="INFO",
            event="rate_ok",
            base=base,
            target=target,
            rate=rate_value,
            latency_ms=latency_ms,
        )

        return jsonify(
            version=SERVICE_VERSION,
            mode="live",
            base=base,
            target=target,
            rate=rate_value,
        )

    except requests.exceptions.Timeout:
        log_event(
            severity="WARNING",
            event="upstream_timeout",
            url=url,
            timeout_seconds=REQUEST_TIMEOUT,
        )

        return jsonify(error="Upstream timeout"), 504

    except requests.exceptions.RequestException as error:
        log_event(
            severity="ERROR",
            event="upstream_http_error",
            detail=str(error),
            url=url,
        )

        return jsonify(error="Upstream HTTP error"), 502

    except (ValueError, KeyError, TypeError) as error:
        log_event(
            severity="ERROR",
            event="response_parsing_error",
            detail=str(error),
            url=url,
        )

        return jsonify(error="Unable to parse upstream response"), 502

    except Exception as error:
        log_event(
            severity="ERROR",
            event="unexpected_error",
            detail=str(error),
            url=url,
        )

        return jsonify(error="Internal service error"), 500
