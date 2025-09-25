"""Transform Mullvad API payloads into structured relay objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Sequence, Set

from .errors import RelayBuildError

SOCKS5_SUFFIX = ".relays.mullvad.net:1080"


@dataclass(slots=True)
class SourcePayload:
    """Wrapper holding a named payload from a relay source."""

    name: str
    payload: dict


@dataclass(slots=True)
class Relay:
    hostname: str
    socks5_hostname: str
    socks5_endpoint: str
    location_id: str
    city: str
    country: str
    provider: str
    ipv4: str
    ipv6: Optional[str]
    weight: int
    owned: bool
    active: bool
    include_in_country: bool
    source: str

    def to_dict(self) -> dict:
        """Return a serialisable dict representation."""
        return asdict(self)


@dataclass(slots=True)
class FilterConfig:
    countries: Optional[Set[str]] = None
    cities: Optional[Set[str]] = None
    include_owned: bool = False
    providers_allow: Optional[Set[str]] = None
    providers_block: Optional[Set[str]] = None
    limit: Optional[int] = None


@dataclass(slots=True)
class FilterSample:
    """Represents a relay excluded by filtering along with the reason."""

    reason: str
    relay: Relay


@dataclass(slots=True)
class FilterReport:
    """Details about filter execution for diagnostics."""

    unmatched_filters: List[str]
    excluded_samples: List[FilterSample]


def build_relays(payloads: Sequence[SourcePayload]) -> List[Relay]:
    """Construct Relay objects from multiple source payloads."""

    relays: List[Relay] = []
    for source_payload in payloads:
        try:
            raw_relays: Sequence[dict] = source_payload.payload["wireguard"]["relays"]
            locations: dict = source_payload.payload["locations"]
        except KeyError as exc:  # pragma: no cover - guard for schema drift
            raise RelayBuildError(
                f"Unexpected payload structure for source {source_payload.name}"
            ) from exc

        relays.extend(
            _build_relays_for_source(
                source=source_payload.name,
                raw_relays=raw_relays,
                locations=locations,
            )
        )

    return relays


def _build_relays_for_source(
    *, source: str, raw_relays: Sequence[dict], locations: dict
) -> List[Relay]:
    relays: List[Relay] = []
    for relay in raw_relays:
        location_id = relay.get("location")
        if not location_id:
            continue
        location = locations.get(location_id, {})
        city = location.get("city", "")
        country = location.get("country", "")
        hostname = relay.get("hostname")
        if not hostname:
            continue
        if "-wg-" in hostname:
            socks5_hostname = hostname.replace("-wg-", "-wg-socks5-", 1)
        else:
            socks5_hostname = f"{hostname}-socks5"
        socks5_endpoint = f"{socks5_hostname}{SOCKS5_SUFFIX}"
        relays.append(
            Relay(
                hostname=hostname,
                socks5_hostname=socks5_hostname,
                socks5_endpoint=socks5_endpoint,
                location_id=location_id,
                city=city,
                country=country,
                provider=relay.get("provider", ""),
                ipv4=relay.get("ipv4_addr_in", ""),
                ipv6=relay.get("ipv6_addr_in"),
                weight=int(relay.get("weight", 0) or 0),
                owned=bool(relay.get("owned", False)),
                active=bool(relay.get("active", False)),
                include_in_country=bool(relay.get("include_in_country", False)),
                source=source,
            )
        )
    return relays


def filter_relays(
    relays: Iterable[Relay], config: FilterConfig
) -> tuple[List[Relay], FilterReport]:
    """Filter relays according to the provided configuration."""

    countries = {value.lower() for value in config.countries} if config.countries else None
    cities = {value.lower() for value in config.cities} if config.cities else None
    allow = {value.lower() for value in config.providers_allow} if config.providers_allow else None
    block = {value.lower() for value in config.providers_block} if config.providers_block else None

    unmatched: List[str] = []
    excluded_samples: List[FilterSample] = []

    def record_sample(reason: str, relay: Relay) -> None:
        if len(excluded_samples) < 10:
            excluded_samples.append(FilterSample(reason=reason, relay=relay))

    filtered: List[Relay] = []
    for relay in relays:
        if not relay.active or not relay.include_in_country:
            continue
        if not config.include_owned and relay.owned:
            continue
        if countries and not _matches_country(relay, countries):
            record_sample("countries", relay)
            continue
        if cities and not _matches_city(relay, cities):
            record_sample("cities", relay)
            continue
        provider_lower = relay.provider.lower()
        if block and provider_lower in block:
            record_sample("providers_block", relay)
            continue
        if allow and provider_lower not in allow:
            record_sample("providers_allow", relay)
            continue
        filtered.append(relay)

    matched_relays = list(filtered)

    if countries and not any(_matches_country(relay, countries) for relay in matched_relays):
        unmatched.extend(f"countries:{value}" for value in config.countries)
    if cities and not any(_matches_city(relay, cities) for relay in matched_relays):
        unmatched.extend(f"cities:{value}" for value in config.cities)
    if allow and not any(relay.provider.lower() in allow for relay in matched_relays):
        unmatched.extend(f"providers_allow:{value}" for value in config.providers_allow)

    filtered.sort(key=lambda item: (item.country.lower(), item.city.lower(), item.hostname, item.source))

    if config.limit is not None and config.limit >= 0:
        filtered = filtered[: config.limit]

    return filtered, FilterReport(
        unmatched_filters=unmatched,
        excluded_samples=excluded_samples,
    )


def format_filter_diagnostics(
    report: FilterReport,
    *,
    remaining_count: int,
    limit: int = 5,
) -> tuple[str, List[str]]:
    """Return a human-readable description and sample diagnostics for filtering."""

    if not report.unmatched_filters and not report.excluded_samples:
        return "", []

    message_parts: List[str] = []
    if report.unmatched_filters:
        summary = ", ".join(report.unmatched_filters)
        message_parts.append(f"Unmatched filter tokens: {summary}.")
    message_parts.append(f"Remaining {remaining_count} relays after filtering.")
    description = " " .join(message_parts)

    samples: List[str] = []
    for sample in report.excluded_samples[:limit]:
        relay = sample.relay
        samples.append(
            f"Excluded ({sample.reason}): {relay.socks5_endpoint} "
            f"({relay.city}, {relay.country}, provider={relay.provider})"
        )

    return description, samples


def _matches_country(relay: Relay, countries: Set[str]) -> bool:
    location_id_lower = relay.location_id.lower()
    country_lower = relay.country.lower()
    prefix = location_id_lower.split("-", 1)[0]
    for value in countries:
        lower = value.lower()
        if lower == country_lower:
            return True
        if lower == location_id_lower:
            return True
        if len(lower) == 2 and lower == prefix:
            return True
    return False


def _matches_city(relay: Relay, cities: Set[str]) -> bool:
    location_id_lower = relay.location_id.lower()
    city_lower = relay.city.lower()
    for value in cities:
        lower = value.lower()
        if lower == city_lower:
            return True
        if lower == location_id_lower:
            return True
    return False


__all__ = [
    "Relay",
    "FilterConfig",
    "FilterReport",
    "FilterSample",
    "SourcePayload",
    "SOCKS5_SUFFIX",
    "build_relays",
    "filter_relays",
    "format_filter_diagnostics",
]
