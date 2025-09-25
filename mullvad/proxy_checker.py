"""Integration helpers for Proxy Scraper Checker outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .errors import RelayBuildError
from .enrich import ProxyChecker
from .transform import Relay

INSTALL_GUIDANCE = (
    "Install via `mise install --from "
    "git+https://github.com/monosans/proxy-scraper-checker.git --language=rust "
    "proxy-scraper-checker` or provide --proxy-checker-bin."
)


class ProxyScraperChecker(ProxyChecker):
    """Invoke Proxy Scraper Checker to augment relays with external verdicts."""

    def __init__(
        self,
        *,
        binary: str | None = None,
        args: Optional[Sequence[str]] = None,
        timeout: int = 60,
        export_path: Path | None = None,
    ) -> None:
        self.binary = binary
        self.args = list(args or [])
        self.timeout = timeout
        self.export_path = export_path
        if self.export_path is not None and not self.export_path.exists():
            raise FileNotFoundError(
                f"Proxy Scraper Checker export not found: {self.export_path}"
            )

    def enrich(self, relays: Iterable[Relay]) -> tuple[Optional[dict], List[dict]]:
        relays_list = list(relays)
        if not relays_list:
            return None, []

        data = self._load_export(relays_list)

        mapping: dict[str, dict] = {}
        for item in data:
            endpoint = self._extract_endpoint(item)
            if not endpoint:
                continue
            metadata = {
                "socks5_endpoint": endpoint,
                "availability": item.get("status")
                or item.get("availability")
                or item.get("alive"),
                "latency_ms": item.get("latency_ms")
                or item.get("latency")
                or item.get("ping"),
                "country": item.get("country"),
                "city": item.get("city"),
                "source": item.get("source"),
                "protocol": item.get("protocol"),
            }
            mapping[endpoint] = metadata

        summary = {
            "source": "proxy-scraper-checker",
            "total_entries": len(data),
            "matched": len(mapping),
        }
        if self.binary is not None:
            summary["binary"] = self.binary
            summary["args"] = self.args
            summary["timeout"] = self.timeout
        if self.export_path is not None:
            summary["export_path"] = str(self.export_path)

        details = list(mapping.values())
        return summary, details

    def _load_export(self, relays: List[Relay]) -> List[dict]:
        raw_json: str
        if self.export_path is not None:
            raw_json = self.export_path.read_text()
        else:
            raw_json = self._run_checker(relays)

        try:
            raw = json.loads(raw_json)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise RelayBuildError(
                "Proxy Scraper Checker returned invalid JSON output"
            ) from exc

        if isinstance(raw, dict):
            for key in ("proxies", "socks5", "items"):
                if key in raw and isinstance(raw[key], list):
                    return [self._normalise_item(item) for item in raw[key] if isinstance(item, dict)]
            return [self._normalise_item(raw)]
        if isinstance(raw, list):
            return [self._normalise_item(item) for item in raw if isinstance(item, dict)]
        raise RelayBuildError("Unsupported proxy checker export format")

    def _normalise_item(self, item: dict) -> dict:
        return item

    def _extract_endpoint(self, item: dict) -> Optional[str]:
        if "socks5_endpoint" in item:
            return str(item["socks5_endpoint"])
        if "endpoint" in item:
            return str(item["endpoint"])
        if "proxy" in item:
            value = str(item["proxy"])
            if "socks5://" in value:
                return value.split("socks5://", 1)[1]
            if value.startswith("socks5") and "://" in value:
                return value.split("://", 1)[1]
            if value and ":" in value and "://" not in value:
                return value
        protocol = str(item.get("protocol") or item.get("type") or "").lower()
        if protocol == "socks5":
            host = item.get("host") or item.get("ip") or item.get("address")
            port = item.get("port")
            if host and port:
                return f"{host}:{port}"
        return None

    def _run_checker(self, relays: List[Relay]) -> str:
        if self.binary is None:
            raise RelayBuildError(
                "Proxy Scraper Checker binary not configured. Provide --proxy-checker-bin or "
                "set export_path with recorded output."
            )

        binary_path = Path(self.binary)
        if not binary_path.exists():
            resolved = shutil.which(self.binary)
            if resolved is None:
                raise RelayBuildError(
                    "Proxy Scraper Checker binary not found. " + INSTALL_GUIDANCE
                )
            binary_path = Path(resolved)

        endpoints_input = "\n".join(relay.socks5_endpoint for relay in relays)

        try:
            completed = subprocess.run(
                [str(binary_path), *self.args],
                input=endpoints_input,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - safety
            raise RelayBuildError(
                "Proxy Scraper Checker binary could not be executed"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RelayBuildError(
                f"Proxy Scraper Checker timed out after {self.timeout}s"
            ) from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            details = stderr or stdout or "no additional output"
            raise RelayBuildError(
                f"Proxy Scraper Checker exited with code {completed.returncode}: {details}"
            )

        output = completed.stdout.strip()
        if not output:
            raise RelayBuildError("Proxy Scraper Checker returned empty output")
        return output


__all__ = ["ProxyScraperChecker"]
