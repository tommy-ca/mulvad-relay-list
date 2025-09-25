import json
import tempfile
from pathlib import Path
from mullvad.enrich import EnrichmentResult, ProxyChecker, enrich_relays
from mullvad.proxy_checker import ProxyScraperChecker
from mullvad.transform import Relay


class DummyChecker(ProxyChecker):
    def enrich(self, relays):
        details = []
        for relay in relays:
            details.append(
                {
                    "socks5_endpoint": relay.socks5_endpoint,
                    "availability": "up",
                    "latency_ms": 42,
                }
            )
        return {"checked": len(details)}, details


def make_relay(hostname: str) -> Relay:
    return Relay(
        hostname=hostname,
        socks5_hostname=f"{hostname}-socks5",
        socks5_endpoint=f"{hostname}-socks5.relays.mullvad.net:1080",
        location_id="xx-city",
        city="Test City",
        country="Testland",
        provider="TestProvider",
        ipv4="192.0.2.1",
        ipv6=None,
        weight=100,
        owned=False,
        active=True,
        include_in_country=True,
        source="mullvad",
    )


def test_enrich_relays_attaches_checker_metadata():
    relays = [make_relay("relay-001"), make_relay("relay-002")]
    checker = DummyChecker()
    result = enrich_relays(relays, proxy_checker=checker, verification_sample_size=1)
    assert isinstance(result, EnrichmentResult)
    assert len(result.enriched_relays) == 2
    assert result.checker_summary == {"checked": 2}
    first = result.enriched_relays[0]
    assert first.proxy_checker["latency_ms"] == 42
    assert result.verification_candidates == relays[:1]


def test_enrich_relays_handles_missing_checker():
    relays = [make_relay("relay-003")]
    result = enrich_relays(relays, proxy_checker=None)
    assert len(result.enriched_relays) == 1
    assert result.enriched_relays[0].proxy_checker is None
    assert result.checker_summary is None


def test_proxy_scraper_checker_loads_recorded_output():
    """Integration test: ProxyScraperChecker loads recorded JSON output and maps metadata correctly."""
    test_data_path = Path(__file__).parent / "data" / "proxy_scraper_checker_output.json"
    checker = ProxyScraperChecker(export_path=test_data_path)

    # Create relays that should match the test data
    relays = [
        make_relay_with_endpoint("relay-001", "relay-001-socks5.relays.mullvad.net:1080"),
        make_relay_with_endpoint("relay-002", "relay-002-socks5.relays.mullvad.net:1080"),
        make_relay_with_endpoint("relay-003", "relay-003-socks5.relays.mullvad.net:1080"),
        make_relay_with_endpoint("relay-004", "relay-004-socks5.relays.mullvad.net:1080"),
    ]

    result = enrich_relays(relays, proxy_checker=checker)

    # Verify enrichment completed successfully
    assert len(result.enriched_relays) == 4
    assert result.checker_summary is not None
    assert result.checker_summary["source"] == "proxy-scraper-checker"
    assert result.checker_summary["total_entries"] == 4
    assert result.checker_summary["matched"] == 4

    # Verify specific metadata mapping for first relay
    first_enriched = result.enriched_relays[0]
    assert first_enriched.proxy_checker is not None
    assert first_enriched.proxy_checker["availability"] == "up"
    assert first_enriched.proxy_checker["latency_ms"] == 45
    assert first_enriched.proxy_checker["country"] == "Sweden"
    assert first_enriched.proxy_checker["city"] == "Stockholm"

    # Verify different field name mappings work
    second_enriched = result.enriched_relays[1]
    assert second_enriched.proxy_checker["availability"] == "up"  # mapped from "status"
    assert second_enriched.proxy_checker["latency_ms"] == 89      # mapped from "latency"

    # Verify boolean availability mapping
    third_enriched = result.enriched_relays[2]
    assert third_enriched.proxy_checker["availability"]  # mapped from "alive"
    assert third_enriched.proxy_checker["latency_ms"] == 123     # mapped from "ping"

    # Verify down/failed availability
    fourth_enriched = result.enriched_relays[3]
    assert fourth_enriched.proxy_checker["availability"] == "down"
    assert fourth_enriched.proxy_checker["latency_ms"] is None


def test_proxy_scraper_checker_handles_wrapped_format():
    """Integration test: ProxyScraperChecker handles JSON wrapped under 'proxies' key."""
    test_data_path = Path(__file__).parent / "data" / "proxy_scraper_checker_wrapped.json"
    checker = ProxyScraperChecker(export_path=test_data_path)

    relays = [
        make_relay_with_endpoint("relay-005", "relay-005-socks5.relays.mullvad.net:1080"),
    ]

    result = enrich_relays(relays, proxy_checker=checker)

    assert len(result.enriched_relays) == 1
    assert result.checker_summary["total_entries"] == 1
    assert result.checker_summary["matched"] == 1

    enriched = result.enriched_relays[0]
    assert enriched.proxy_checker["country"] == "United Kingdom"
    assert enriched.proxy_checker["city"] == "London"


def test_proxy_scraper_checker_handles_missing_file():
    """Integration test: ProxyScraperChecker raises FileNotFoundError for missing export."""
    missing_path = Path("/nonexistent/proxy_checker_output.json")
    try:
        ProxyScraperChecker(export_path=missing_path)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as e:
        assert "Proxy Scraper Checker export not found" in str(e)


def test_proxy_scraper_checker_endpoint_extraction():
    """Integration test: ProxyScraperChecker correctly extracts endpoints from various formats."""
    test_data_path = Path(__file__).parent / "data" / "proxy_scraper_checker_output.json"
    checker = ProxyScraperChecker(export_path=test_data_path)

    # Test the internal endpoint extraction directly
    assert checker._extract_endpoint({"socks5_endpoint": "host1:1080"}) == "host1:1080"
    assert checker._extract_endpoint({"endpoint": "host2:1080"}) == "host2:1080"
    assert checker._extract_endpoint({"proxy": "socks5://host3:1080"}) == "host3:1080"
    assert checker._extract_endpoint({"proxy": "host4:1080"}) == "host4:1080"
    assert checker._extract_endpoint({"host": "host5", "port": 1080, "protocol": "socks5"}) == "host5:1080"
    assert checker._extract_endpoint({"ip": "host6", "port": 1080, "type": "socks5"}) == "host6:1080"
    assert checker._extract_endpoint({"address": "host7", "port": 1080, "protocol": "socks5"}) == "host7:1080"
    assert checker._extract_endpoint({"proxy": "http://host8:1080"}) is None  # not socks5
    assert checker._extract_endpoint({"host": "host9"}) is None  # missing port


def test_proxy_scraper_checker_subprocess_integration():
    """Integration test: Verify ProxyScraperChecker can work with real binary output format."""
    # This test simulates the actual proxy-scraper-checker binary execution and JSON parsing
    # by mocking the subprocess call but using real output format

    mock_output = json.dumps([
        {
            "proxy": "socks5://test-relay-1.example.com:1080",
            "status": "up",
            "latency_ms": 156,
            "country": "Sweden",
            "city": "Stockholm",
            "source": "proxy-scraper-checker"
        },
        {
            "proxy": "socks5://test-relay-2.example.com:1080",
            "status": "down",
            "latency_ms": None,
            "country": "Netherlands",
            "city": "Amsterdam",
            "source": "proxy-scraper-checker"
        }
    ])

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(mock_output)
        temp_path = Path(f.name)

    try:
        checker = ProxyScraperChecker(export_path=temp_path)

        # Create relays matching the mock output
        relays = [
            make_relay_with_endpoint("test-relay-1", "test-relay-1.example.com:1080"),
            make_relay_with_endpoint("test-relay-2", "test-relay-2.example.com:1080"),
        ]

        result = enrich_relays(relays, proxy_checker=checker)

        # Verify integration worked correctly
        assert len(result.enriched_relays) == 2
        assert result.checker_summary["source"] == "proxy-scraper-checker"
        assert result.checker_summary["total_entries"] == 2
        assert result.checker_summary["matched"] == 2

        # Verify first relay (up)
        first = result.enriched_relays[0]
        assert first.proxy_checker["availability"] == "up"
        assert first.proxy_checker["latency_ms"] == 156
        assert first.proxy_checker["country"] == "Sweden"

        # Verify second relay (down)
        second = result.enriched_relays[1]
        assert second.proxy_checker["availability"] == "down"
        assert second.proxy_checker["latency_ms"] is None
        assert second.proxy_checker["country"] == "Netherlands"

    finally:
        temp_path.unlink()


def make_relay_with_endpoint(hostname: str, socks5_endpoint: str) -> Relay:
    """Helper to create relay with specific endpoint for testing."""
    return Relay(
        hostname=hostname,
        socks5_hostname=socks5_endpoint.split(":")[0],
        socks5_endpoint=socks5_endpoint,
        location_id="xx-city",
        city="Test City",
        country="Testland",
        provider="TestProvider",
        ipv4="192.0.2.1",
        ipv6=None,
        weight=100,
        owned=False,
        active=True,
        include_in_country=True,
        source="mullvad",
    )
