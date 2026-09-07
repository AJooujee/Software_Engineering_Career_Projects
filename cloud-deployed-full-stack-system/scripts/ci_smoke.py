"""Validate the production-like Compose stack without external packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message


@dataclass(frozen=True)
class Response:
    """Small HTTP response value used by the smoke assertions."""

    status: int
    headers: Message
    body: bytes


def fetch_with_retry(url: str, timeout_seconds: float) -> Response:
    """Fetch one URL, retrying while the Compose services become ready."""

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "cloud-operations-ci-smoke"},
            )

            with urllib.request.urlopen(request, timeout=5) as response:
                return Response(
                    status=response.status,
                    headers=response.headers,
                    body=response.read(),
                )
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
        ) as error:
            last_error = error
            time.sleep(2)

    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def require(condition: bool, message: str) -> None:
    """Raise a readable smoke-test failure when a condition is false."""

    if not condition:
        raise RuntimeError(message)


def require_status(response: Response, url: str) -> None:
    """Require a successful HTTP status."""

    require(
        response.status == 200,
        f"Expected HTTP 200 from {url}, received {response.status}.",
    )


def require_security_headers(response: Response, label: str) -> None:
    """Require the Nginx security headers on one proxied response."""

    expected = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    for header, value in expected.items():
        actual = response.headers.get(header)
        require(
            actual == value,
            f"{label} returned {header}={actual!r}; expected {value!r}.",
        )


def validate(frontend_url: str, backend_url: str, timeout: float) -> None:
    """Validate health, API discovery, SPA routing, assets, and headers."""

    frontend_url = frontend_url.rstrip("/")
    backend_url = backend_url.rstrip("/")

    direct_health_url = f"{backend_url}/health"
    proxy_health_url = f"{frontend_url}/health"
    dashboard_url = f"{frontend_url}/dashboard"
    fallback_url = f"{frontend_url}/phase-8-ci-fallback"
    openapi_url = f"{frontend_url}/openapi.json"

    direct_health = fetch_with_retry(direct_health_url, timeout)
    require_status(direct_health, direct_health_url)
    direct_payload = json.loads(direct_health.body)
    require(
        direct_payload.get("status") == "healthy",
        "Direct backend health payload is not healthy.",
    )

    proxy_health = fetch_with_retry(proxy_health_url, timeout)
    require_status(proxy_health, proxy_health_url)
    proxy_payload = json.loads(proxy_health.body)
    require(
        proxy_payload.get("status") == "healthy",
        "Nginx proxy health payload is not healthy.",
    )
    require_security_headers(proxy_health, "Proxy health response")

    dashboard = fetch_with_retry(dashboard_url, timeout)
    require_status(dashboard, dashboard_url)
    require_security_headers(dashboard, "Dashboard response")
    dashboard_html = dashboard.body.decode("utf-8")

    fallback = fetch_with_retry(fallback_url, timeout)
    require_status(fallback, fallback_url)
    require_security_headers(fallback, "SPA fallback response")
    require(
        fallback.body == dashboard.body,
        "SPA fallback did not return the production entry point.",
    )

    asset_match = re.search(
        r'''<script[^>]+src=["']([^"']+\.js)["']''',
        dashboard_html,
    )
    require(asset_match is not None, "No JavaScript bundle was found.")
    asset_url = urllib.parse.urljoin(
        f"{frontend_url}/",
        asset_match.group(1),
    )
    asset = fetch_with_retry(asset_url, timeout)
    require_status(asset, asset_url)
    require_security_headers(asset, "JavaScript asset response")

    cache_control = ",".join(
        asset.headers.get_all("Cache-Control", [])
    ).lower()

    for directive in ("public", "immutable", "max-age=31536000"):
        require(
            directive in cache_control,
            f"JavaScript asset is missing Cache-Control {directive!r}.",
        )

    openapi = fetch_with_retry(openapi_url, timeout)
    require_status(openapi, openapi_url)
    require_security_headers(openapi, "OpenAPI response")
    openapi_payload = json.loads(openapi.body)
    available_paths = set(openapi_payload.get("paths", {}))
    required_paths = {
        "/api/audit-events",
        "/api/dashboard/summary",
        "/api/incidents",
    }
    missing_paths = sorted(required_paths - available_paths)
    require(
        not missing_paths,
        f"OpenAPI document is missing routes: {', '.join(missing_paths)}",
    )

    print("Direct backend health: healthy")
    print("Nginx proxy health: healthy")
    print("SPA fallback: HTTP 200")
    print(f"JavaScript asset: HTTP 200 ({asset_match.group(1)})")
    print("Security headers: present on page, asset, health, and OpenAPI")
    print("Asset caching: public, immutable, max-age=31536000")
    print("Required API paths: present")


def parse_args() -> argparse.Namespace:
    """Parse command-line options used locally and in GitHub Actions."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frontend-url",
        default="http://127.0.0.1:8080",
    )
    parser.add_argument(
        "--backend-url",
        default="http://127.0.0.1:8001",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
    )
    return parser.parse_args()


def main() -> int:
    """Run the smoke validation and return a shell-friendly exit code."""

    args = parse_args()

    try:
        validate(
            frontend_url=args.frontend_url,
            backend_url=args.backend_url,
            timeout=args.timeout,
        )
    except Exception as error:  # noqa: BLE001 - CLI boundary reports all failures.
        print(f"Phase 8 smoke validation failed: {error}", file=sys.stderr)
        return 1

    print("Phase 8 production-stack smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
