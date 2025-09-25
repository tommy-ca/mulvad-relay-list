"""Pipeline orchestration helpers for multi-source relay aggregation."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Callable, Iterable, Iterator, List, Sequence


@dataclass(slots=True)
class SourceResult:
    """Represents the outcome of fetching a single relay source."""

    name: str
    payload: dict | None
    error: Exception | None
    duration: float
    attempts: int
    cache_bypassed: bool


@dataclass(slots=True)
class StageMeasurement:
    """Timing information for a named pipeline stage."""

    name: str
    duration: float


@dataclass(slots=True)
class PipelineStats:
    """Captures timing and diagnostic data across a pipeline run."""

    sla_seconds: float
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    stages: List[StageMeasurement] = field(default_factory=list)
    source_results: List[SourceResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """Context manager to time a pipeline stage."""

        start = perf_counter()
        try:
            yield
        finally:
            duration = perf_counter() - start
            self.stages.append(StageMeasurement(name=name, duration=duration))

    def record_source_results(self, results: Sequence[SourceResult]) -> None:
        self.source_results = list(results)

    def add_note(self, message: str) -> None:
        self.notes.append(message)

    def finish(self) -> None:
        if self.finished_at is None:
            self.finished_at = datetime.now(timezone.utc)

    @property
    def total_duration(self) -> float:
        if self.finished_at is None:
            return sum(measurement.duration for measurement in self.stages)
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def sla_breached(self) -> bool:
        return self.total_duration > self.sla_seconds


class BaseSourceAdapter(ABC):
    """Adapter interface for supplemental relay sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-friendly adapter name used in metrics and diagnostics."""

    @abstractmethod
    def fetch(self, *, force_refresh: bool) -> dict:
        """Return the raw payload for this adapter."""


class SourceManager:
    """Coordinates fetching relay data from Mullvad and optional adapters."""

    def __init__(
        self,
        api_client,
        adapters: Sequence[BaseSourceAdapter] | None = None,
        *,
        retry_delay: float = 0.25,
        max_attempts: int = 2,
    ) -> None:
        self._api_client = api_client
        self._adapters = list(adapters or [])
        self._retry_delay = retry_delay
        self._max_attempts = max(1, max_attempts)

    def fetch_all(self, *, force_refresh: bool = False) -> List[SourceResult]:
        """Fetch Mullvad plus adapter sources, returning ordered results."""

        results: List[SourceResult] = []
        results.append(
            self._fetch_with_retry(
                name="mullvad",
                fetcher=lambda: self._api_client.fetch_wireguard_relays(
                    force_refresh=force_refresh
                ),
                force_refresh=force_refresh,
            )
        )

        for adapter in self._adapters:
            results.append(
                self._fetch_with_retry(
                    name=adapter.name,
                    fetcher=lambda adapter=adapter: adapter.fetch(
                        force_refresh=force_refresh
                    ),
                    force_refresh=force_refresh,
                )
            )

        return results

    def _fetch_with_retry(
        self,
        *,
        name: str,
        fetcher: Callable[[], dict],
        force_refresh: bool,
    ) -> SourceResult:
        attempts = 0
        start = perf_counter()
        last_error: Exception | None = None
        while attempts < self._max_attempts:
            attempts += 1
            try:
                payload = fetcher()
                duration = perf_counter() - start
                return SourceResult(
                    name=name,
                    payload=payload,
                    error=None,
                    duration=duration,
                    attempts=attempts,
                    cache_bypassed=force_refresh,
                )
            except Exception as exc:  # pragma: no cover - exercised via tests
                last_error = exc
                if attempts >= self._max_attempts:
                    break
                if self._retry_delay > 0:
                    time.sleep(self._retry_delay)

        duration = perf_counter() - start
        return SourceResult(
            name=name,
            payload=None,
            error=last_error,
            duration=duration,
            attempts=attempts,
            cache_bypassed=force_refresh,
        )


__all__ = [
    "BaseSourceAdapter",
    "PipelineStats",
    "SourceManager",
    "SourceResult",
    "StageMeasurement",
]
