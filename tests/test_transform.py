import json
from pathlib import Path

import pytest

from mullvad.transform import (
    FilterConfig,
    FilterReport,
    SourcePayload,
    build_relays,
    filter_relays,
    format_filter_diagnostics,
)


@pytest.fixture(scope="module")
def payload():
    sample_path = Path(__file__).parent / "data" / "wireguard_sample.json"
    return json.loads(sample_path.read_text())


def test_build_relays_constructs_socks5_endpoint(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    assert len(relays) == 5
    first = relays[0]
    assert first.hostname == "al-tia-wg-003"
    assert first.socks5_hostname == "al-tia-wg-socks5-003"
    assert first.socks5_endpoint.endswith(".relays.mullvad.net:1080")
    assert first.source == "mullvad"


def test_filter_relays_by_country(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    config = FilterConfig(countries={"Austria"})
    filtered, report = filter_relays(relays, config)
    assert {relay.country for relay in filtered} == {"Austria"}
    assert report.unmatched_filters == []
    assert len(filtered) == 3


def test_filter_relays_limit(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    config = FilterConfig(limit=2)
    filtered, report = filter_relays(relays, config)
    assert len(filtered) == 2
    assert report.unmatched_filters == []


def test_filter_relays_excludes_owned_by_default(payload):
    source_payload = SourcePayload(name="mullvad", payload=payload)
    relays = build_relays([source_payload])
    config = FilterConfig()
    filtered, report = filter_relays(relays, config)
    assert all(not relay.owned for relay in filtered)
    assert report.unmatched_filters == []


def test_filter_relays_includes_owned_when_requested(payload):
    source_payload = SourcePayload(name="mullvad", payload=payload)
    relays = build_relays([source_payload])
    config = FilterConfig(include_owned=True)
    filtered, report = filter_relays(relays, config)
    assert len(filtered) == len(relays)
    assert all(relay.source == "mullvad" for relay in filtered)
    assert report.unmatched_filters == []


def test_filter_reports_unmatched_tokens(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    config = FilterConfig(countries={"mars"})
    filtered, report = filter_relays(relays, config)
    assert filtered == []
    assert report.unmatched_filters == ["countries:mars"]


def test_build_relays_combines_multiple_sources(payload):
    alt_payload = {
        "wireguard": {"relays": []},
        "locations": {},
    }
    relays = build_relays(
        [
            SourcePayload(name="mullvad", payload=payload),
            SourcePayload(name="alt", payload=alt_payload),
        ]
    )
    assert {relay.source for relay in relays} == {"mullvad"}
    assert len(relays) == 5


def test_filter_configs_report_all_unmatched_values(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    config = FilterConfig(countries={"mars"}, providers_allow={"unknown"})
    filtered, report = filter_relays(relays, config)
    assert filtered == []
    assert set(report.unmatched_filters) == {"countries:mars", "providers_allow:unknown"}


def test_format_filter_diagnostics_returns_sample_relays(payload):
    relays = build_relays([SourcePayload(name="mullvad", payload=payload)])
    config = FilterConfig(countries={"mars"})
    filtered, report = filter_relays(relays, config)
    message, samples = format_filter_diagnostics(report, remaining_count=len(filtered), limit=2)
    assert "countries:mars" in message
    assert "Remaining 0 relays" in message
    assert len(samples) <= 2
    if samples:
        assert samples[0].startswith("Excluded (countries)")
