"""Proxy verification helpers wrapping scripts.verify_proxies."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import requests
from websocket import create_connection

from scripts.verify_proxies import (  # type: ignore[import]
    HTTP_TEST_URL,
    WS_TEST_URL,
    ProxyResult,
    verify as run_verify,
)

from .errors import RelayBuildError

MUBENG_INSTALL_GUIDANCE = (
    "Install via `mise install --from git+https://github.com/mubeng/mubeng.git "
    "--language=go mubeng` or provide --mubeng-bin."
)


@dataclass(slots=True)
class VerificationSummary:
    results: List[ProxyResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def http_success(self) -> int:
        return sum(result.http_ok for result in self.results)

    @property
    def ws_success(self) -> int:
        return sum(result.ws_ok for result in self.results)

    @property
    def failures(self) -> List[ProxyResult]:
        return [result for result in self.results if not (result.http_ok and result.ws_ok)]


def preflight_targets(
    http_url: str,
    ws_url: str,
    *,
    timeout: int,
    http_verify: bool | str,
) -> None:
    """Ensure verification targets are reachable before proxy checks."""

    requests.get(http_url, timeout=timeout, verify=http_verify)
    ws = create_connection(ws_url, timeout=timeout)
    try:
        ws.send("ping")
        ws.recv()
    finally:
        ws.close()


def run_proxy_verification(
    endpoints: Iterable[str],
    *,
    timeout: int,
    http_url: str = HTTP_TEST_URL,
    ws_url: str = WS_TEST_URL,
    http_verify: bool | str = True,
) -> VerificationSummary:
    results = run_verify(
        endpoints,
        timeout,
        http_url=http_url,
        ws_url=ws_url,
        http_verify=http_verify,
    )
    return VerificationSummary(results=results)


def summarize_mubeng(summary: VerificationSummary) -> dict:
    """Produce a Mubeng-style summary using gathered verification results."""

    failures = summary.failures
    return {
        "checked": summary.total,
        "ok": not failures,
        "failures": [failure.endpoint for failure in failures],
    }


def run_mubeng(
    endpoints: Iterable[str],
    *,
    binary: str = "mubeng",
    args: Sequence[str] | None = None,
    timeout: int = 60,
) -> dict:
    """Invoke the Mubeng binary to verify SOCKS5 endpoints."""

    endpoints = list(endpoints)
    if not endpoints:
        raise RelayBuildError("No endpoints provided for Mubeng verification")

    binary_path = Path(binary)
    if not binary_path.exists():
        resolved = shutil.which(binary)
        if resolved is None:
            raise RelayBuildError("Mubeng binary not found. " + MUBENG_INSTALL_GUIDANCE)
        binary_path = Path(resolved)

    formatted = [endpoint if endpoint.startswith("socks5://") else f"socks5://{endpoint}" for endpoint in endpoints]
    payload = "\n".join(formatted)
    extra_args = list(args or [])

    try:
        completed = subprocess.run(
            [str(binary_path), *extra_args],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise RelayBuildError("Mubeng binary could not be executed") from exc
    except subprocess.TimeoutExpired as exc:
        raise RelayBuildError(f"Mubeng timed out after {timeout}s") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        details = stderr or stdout or "no additional output"
        raise RelayBuildError(
            f"Mubeng exited with code {completed.returncode}: {details}"
        )

    output = completed.stdout.strip()
    if not output:
        raise RelayBuildError("Mubeng returned empty output")

    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RelayBuildError("Mubeng returned invalid JSON output") from exc

    if not isinstance(report, dict):
        raise RelayBuildError("Mubeng returned unsupported output format")

    report.setdefault("binary", str(binary_path))
    report.setdefault("args", extra_args)
    return report


__all__ = [
    "VerificationSummary",
    "preflight_targets",
    "run_proxy_verification",
    "run_mubeng",
    "summarize_mubeng",
]
