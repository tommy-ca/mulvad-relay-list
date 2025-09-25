"""HTTP client helpers for Mullvad's public relay API."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .errors import RelayBuildError

API_URL = "https://api.mullvad.net/public/relays/wireguard/v2"


class MullvadAPI:
    """Small helper around Mullvad's public API with optional file caching."""

    def __init__(
        self,
        cache_dir: Path | str = Path(".cache"),
        ttl_seconds: int = 300,
        use_cache: bool = True,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._cache_dir = Path(cache_dir)
        self._ttl_seconds = ttl_seconds
        self._use_cache = use_cache
        self._session = session or requests.Session()
        if self._use_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_wireguard_relays(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Return the raw JSON payload from Mullvad's relay endpoint."""

        return self._get_json(API_URL, force_refresh=force_refresh)

    # ------------------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"

    def _get_json(self, url: str, *, force_refresh: bool) -> Dict[str, Any]:
        cache_path = self._cache_path(url)
        if self._use_cache and not force_refresh:
            cached = self._read_cache(cache_path)
            if cached is not None:
                return cached

        try:
            response = self._session.get(url, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover - network error path
            raise RelayBuildError(f"Failed to reach {url}: {exc}") from exc

        if response.status_code != 200:
            raise RelayBuildError(
                f"Unexpected status {response.status_code} from {url}"
            )

        try:
            payload: Dict[str, Any] = response.json()
        except ValueError as exc:  # pragma: no cover - unexpected server response
            raise RelayBuildError("Mullvad API did not return JSON data") from exc

        if self._use_cache:
            self._write_cache(cache_path, payload)

        return payload

    def _read_cache(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > self._ttl_seconds:
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):  # pragma: no cover - corrupt cache
            return None

    def _write_cache(self, path: Path, payload: Dict[str, Any]) -> None:
        try:
            path.write_text(json.dumps(payload))
        except OSError as exc:  # pragma: no cover - disk error
            raise RelayBuildError(f"Failed to write cache {path}: {exc}") from exc


__all__ = ["MullvadAPI", "API_URL"]
