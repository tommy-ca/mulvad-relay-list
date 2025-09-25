import json
from pathlib import Path

import pytest

from mullvad.transform import FilterConfig, Relay, build_relays, filter_relays


@pytest.fixture(scope="module")
def payload():
    sample_path = Path(__file__).parent / "data" / "wireguard_sample.json"
    return json.loads(sample_path.read_text())


def test_build_relays_constructs_socks5_endpoint(payload):
    relays = build_relays(payload)
    assert len(relays) == 5
    first = relays[0]
    assert first.hostname == "al-tia-wg-003"
    assert first.socks5_hostname == "al-tia-wg-socks5-003"
    assert first.socks5_endpoint.endswith(".relays.mullvad.net:1080")


def test_filter_relays_by_country(payload):
    relays = build_relays(payload)
    config = FilterConfig(countries={"Austria"})
    filtered = filter_relays(relays, config)
    assert {relay.country for relay in filtered} == {"Austria"}
    assert len(filtered) == 3


def test_filter_relays_limit(payload):
    relays = build_relays(payload)
    config = FilterConfig(limit=2)
    filtered = filter_relays(relays, config)
    assert len(filtered) == 2


def test_filter_relays_excludes_owned_by_default():
    relays = [
        Relay(
            hostname="test-wg-001",
            socks5_hostname="test-wg-socks5-001",
            socks5_endpoint="test-wg-socks5-001.relays.mullvad.net:1080",
            location_id="xx-city",
            city="Test City",
            country="Testland",
            provider="TestProvider",
            ipv4="192.0.2.1",
            ipv6=None,
            weight=100,
            owned=True,
            active=True,
            include_in_country=True,
        )
    ]
    config = FilterConfig()
    filtered = filter_relays(relays, config)
    assert filtered == []


def test_filter_relays_includes_owned_when_requested():
    relay_owned = Relay(
        hostname="test-wg-002",
        socks5_hostname="test-wg-socks5-002",
        socks5_endpoint="test-wg-socks5-002.relays.mullvad.net:1080",
        location_id="xx-city",
        city="Test City",
        country="Testland",
        provider="TestProvider",
        ipv4="192.0.2.2",
        ipv6=None,
        weight=100,
        owned=True,
        active=True,
        include_in_country=True,
    )
    config = FilterConfig(include_owned=True)
    filtered = filter_relays([relay_owned], config)
    assert filtered == [relay_owned]
