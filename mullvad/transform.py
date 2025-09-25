"""Transform Mullvad API payloads into structured relay objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Sequence, Set

from .errors import RelayBuildError

SOCKS5_SUFFIX = ".relays.mullvad.net:1080"


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


def build_relays(payload: dict) -> List[Relay]:
    """Construct Relay objects from Mullvad API payload."""

    try:
        raw_relays: Sequence[dict] = payload["wireguard"]["relays"]
        locations: dict = payload["locations"]
    except KeyError as exc:  # pragma: no cover - guard for schema drift
        raise RelayBuildError("Unexpected Mullvad API payload structure") from exc

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
            )
        )
    return relays


def filter_relays(relays: Iterable[Relay], config: FilterConfig) -> List[Relay]:
    """Filter relays according to the provided configuration."""

    countries = {value.lower() for value in config.countries} if config.countries else None
    cities = {value.lower() for value in config.cities} if config.cities else None
    allow = {value.lower() for value in config.providers_allow} if config.providers_allow else None
    block = {value.lower() for value in config.providers_block} if config.providers_block else None

    filtered: List[Relay] = []
    for relay in relays:
        if not relay.active or not relay.include_in_country:
            continue
        if not config.include_owned and relay.owned:
            continue
        if countries and not _matches_country(relay, countries):
            continue
        if cities and not _matches_city(relay, cities):
            continue
        provider_lower = relay.provider.lower()
        if block and provider_lower in block:
            continue
        if allow and provider_lower not in allow:
            continue
        filtered.append(relay)

    filtered.sort(key=lambda item: (item.country.lower(), item.city.lower(), item.hostname))

    if config.limit is not None and config.limit >= 0:
        filtered = filtered[: config.limit]

    return filtered


def _matches_country(relay: Relay, countries: Set[str]) -> bool:
    location_id_lower = relay.location_id.lower()
    country_lower = relay.country.lower()
    prefix = location_id_lower.split("-", 1)[0]
    for value in countries:
        if value == country_lower:
            return True
        if value == location_id_lower:
            return True
        if len(value) == 2 and value == prefix:
            return True
    return False


def _matches_city(relay: Relay, cities: Set[str]) -> bool:
    location_id_lower = relay.location_id.lower()
    city_lower = relay.city.lower()
    for value in cities:
        if value == city_lower:
            return True
        if value == location_id_lower:
            return True
    return False


__all__ = [
    "Relay",
    "FilterConfig",
    "SOCKS5_SUFFIX",
    "build_relays",
    "filter_relays",
]
