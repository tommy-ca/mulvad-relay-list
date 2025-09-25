#!/usr/bin/env python3
"""Verify Mullvad SOCKS5 proxies for HTTP, HTTPS, and WebSocket clients."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple, Union

import requests
from websocket import create_connection

HTTP_TEST_URL = "https://httpbin.org/ip"
WS_TEST_URL = "wss://ws.postman-echo.com/raw"
VerifyOption = Union[bool, str, Path]


@dataclass
class ProxyResult:
    endpoint: str
    http_ok: bool
    http_error: str | None
    http_origin: str | None
    ws_ok: bool
    ws_error: str | None


def load_endpoints(json_path: Path, limit: int | None = None) -> List[str]:
    data = json.loads(json_path.read_text())
    endpoints = [item["socks5_endpoint"] for item in data]
    if limit is not None:
        endpoints = endpoints[:limit]
    return endpoints


def test_http(
    endpoint: str,
    timeout: int,
    *,
    url: str = HTTP_TEST_URL,
    verify: VerifyOption = True,
) -> Tuple[bool, str | None, str | None]:
    proxies = {
        "http": f"socks5h://{endpoint}",
        "https": f"socks5h://{endpoint}",
    }
    try:
        response = requests.get(url, proxies=proxies, timeout=timeout, verify=verify)
        origin = None
        if response.ok:
            try:
                data = response.json()
                if isinstance(data, dict):
                    origin = data.get("origin") or data.get("ip")
            except Exception:
                origin = None
            return True, None, origin
        return False, f"HTTP {response.status_code}", None
    except Exception as exc:  # pragma: no cover - network dependent
        return False, str(exc), None


def test_ws(
    endpoint: str,
    timeout: int,
    *,
    url: str = WS_TEST_URL,
) -> Tuple[bool, str | None]:
    host, _, port = endpoint.partition(":")
    try:
        ws = create_connection(
            url,
            timeout=timeout,
            http_proxy_host=host,
            http_proxy_port=int(port or "1080"),
            proxy_type="socks5",
        )
        try:
            ws.send("ping")
            reply = ws.recv()
            return reply == "ping", None if reply == "ping" else f"Unexpected reply: {reply!r}"
        finally:
            ws.close()
    except Exception as exc:  # pragma: no cover - network dependent
        return False, str(exc)


def verify(
    endpoints: Iterable[str],
    timeout: int,
    *,
    http_url: str = HTTP_TEST_URL,
    ws_url: str = WS_TEST_URL,
    http_verify: VerifyOption = True,
) -> List[ProxyResult]:
    results: List[ProxyResult] = []
    for endpoint in endpoints:
        http_ok, http_error, http_origin = test_http(
            endpoint,
            timeout,
            url=http_url,
            verify=http_verify,
        )
        ws_ok, ws_error = test_ws(endpoint, timeout, url=ws_url)
        results.append(
            ProxyResult(
                endpoint=endpoint,
                http_ok=http_ok,
                http_error=http_error,
                http_origin=http_origin,
                ws_ok=ws_ok,
                ws_error=ws_error,
            )
        )
    return results



# Prevent pytest from collecting these helpers as test cases when imported.
test_http.__test__ = False  # type: ignore[attr-defined]
test_ws.__test__ = False  # type: ignore[attr-defined]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        default=Path("build/mullvad_relays.json"),
        type=Path,
        help="Path to JSON relay list",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of proxies to test",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=8,
        help="Timeout (seconds) for each network check",
    )
    parser.add_argument(
        "--http-url",
        default=HTTP_TEST_URL,
        help="HTTP(S) URL to probe through each proxy (default: %(default)s)",
    )
    parser.add_argument(
        "--ws-url",
        default=WS_TEST_URL,
        help="WebSocket URL to probe through each proxy (default: %(default)s)",
    )
    parser.add_argument(
        "--http-ca",
        type=Path,
        help="Path to CA bundle for the HTTPS probe (optional)",
    )
    parser.add_argument(
        "--http-insecure",
        action="store_true",
        help="Skip TLS verification for the HTTP probe (not recommended)",
    )
    args = parser.parse_args()

    http_verify: VerifyOption
    if args.http_insecure:
        http_verify = False
    elif args.http_ca is not None:
        http_verify = args.http_ca
    else:
        http_verify = True

    endpoints = load_endpoints(args.json, args.limit)
    if not endpoints:
        print("No endpoints to verify")
        return 1

    print(f"HTTP target: {args.http_url}")
    print(f"WebSocket target: {args.ws_url}")

    results = verify(
        endpoints,
        args.timeout,
        http_url=args.http_url,
        ws_url=args.ws_url,
        http_verify=http_verify,
    )
    success_http = sum(result.http_ok for result in results)
    success_ws = sum(result.ws_ok for result in results)

    print(f"HTTP success: {success_http}/{len(results)}")
    print(f"WebSocket success: {success_ws}/{len(results)}")

    for result in results:
        print("-", result.endpoint)
        if result.http_ok:
            origin = f" (origin {result.http_origin})" if result.http_origin else ""
            print(f"    HTTP: OK{origin}")
        else:
            print(f"    HTTP: FAIL ({result.http_error})")
        if result.ws_ok:
            print("    WS: OK")
        else:
            print(f"    WS: FAIL ({result.ws_error})")

    return 0 if success_http and success_ws else 2


if __name__ == "__main__":
    raise SystemExit(main())
