"""Relay enrichment helpers for attaching downstream metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .transform import Relay


@dataclass(slots=True)
class EnrichedRelay:
    """Relay enriched with computed metadata."""

    relay: Relay
    availability: Optional[str]
    display_label: str
    proxy_checker: Optional[dict]

    def to_dict(self) -> dict:
        data = self.relay.to_dict()
        data["display_label"] = self.display_label
        if self.availability is not None:
            data["availability"] = self.availability
        if self.proxy_checker is not None:
            data["proxy_checker"] = self.proxy_checker
        return data


@dataclass(slots=True)
class EnrichmentResult:
    enriched_relays: List[EnrichedRelay]
    verification_candidates: List[Relay]
    checker_summary: Optional[dict]


class ProxyChecker:
    """Interface for external proxy checkers such as Proxy Scraper Checker."""

    def enrich(self, relays: Iterable[Relay]) -> tuple[Optional[dict], List[dict]]:
        """Return summary metadata and per-relay details."""

        raise NotImplementedError


def enrich_relays(
    relays: Iterable[Relay],
    *,
    proxy_checker: ProxyChecker | None = None,
    verification_sample_size: int | None = None,
) -> EnrichmentResult:
    relays_list = list(relays)
    checker_map: dict[str, dict] = {}
    summary: Optional[dict] = None

    if proxy_checker is not None and relays_list:
        summary, details = proxy_checker.enrich(relays_list)
        checker_map = {}
        for detail in details:
            endpoint = detail.get("socks5_endpoint") or detail.get("endpoint")
            if not endpoint:
                continue
            checker_map[endpoint] = detail

    enriched: List[EnrichedRelay] = []
    for relay in relays_list:
        metadata = checker_map.get(relay.socks5_endpoint)
        enriched.append(
            EnrichedRelay(
                relay=relay,
                availability=metadata.get("availability") if metadata else None,
                display_label=f"{relay.city}, {relay.country} ({relay.provider})",
                proxy_checker=metadata,
            )
        )

    candidates = relays_list
    if verification_sample_size is not None and verification_sample_size > 0:
        candidates = relays_list[:verification_sample_size]

    return EnrichmentResult(
        enriched_relays=enriched,
        verification_candidates=candidates,
        checker_summary=summary,
    )


__all__ = [
    "EnrichedRelay",
    "EnrichmentResult",
    "ProxyChecker",
    "enrich_relays",
]
