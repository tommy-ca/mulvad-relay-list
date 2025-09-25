from pathlib import Path

from mullvad.output import write_pac
from mullvad.transform import Relay


def _relay(hostname: str) -> Relay:
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
    )


def test_write_pac_includes_proxies(tmp_path: Path) -> None:
    destination = tmp_path / "relays.pac"
    relays = [_relay("relay-001"), _relay("relay-002")]
    write_pac(relays, destination)

    content = destination.read_text()

    assert "FindProxyForURL" in content
    assert '"SOCKS5 relay-001-socks5.relays.mullvad.net:1080"' in content
    assert '"SOCKS5 relay-002-socks5.relays.mullvad.net:1080"' in content
    assert "return proxies[index];" in content


def test_write_pac_handles_empty(tmp_path: Path) -> None:
    destination = tmp_path / "empty.pac"
    write_pac([], destination)

    content = destination.read_text()

    assert 'var proxies = [' in content
    assert 'return "DIRECT";' in content
