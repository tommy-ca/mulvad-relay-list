import hashlib
import json
from pathlib import Path

from mullvad.output import write_pac, write_text, write_csv, write_manifest
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
        source="test",
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


def test_write_text_outputs_host_port_pairs(tmp_path: Path) -> None:
    destination = tmp_path / "relays.txt"
    relays = [_relay("relay-001"), _relay("relay-002")]

    write_text(relays, destination)

    lines = destination.read_text().splitlines()
    assert lines == [
        "socks5://relay-001-socks5.relays.mullvad.net:1080",
        "socks5://relay-002-socks5.relays.mullvad.net:1080",
    ]


def test_write_csv_produces_expected_columns(tmp_path: Path) -> None:
    destination = tmp_path / "relays.csv"
    relays = [_relay("relay-001"), _relay("relay-002")]

    write_csv(relays, destination)

    content = destination.read_text().splitlines()
    assert content[0] == (
        "hostname,socks5_hostname,socks5_endpoint,city,country,"  # noqa: E501
        "provider,ipv4,ipv6"
    )
    assert content[1] == (
        "relay-001,relay-001-socks5,relay-001-socks5.relays.mullvad.net:1080,"
        "Test City,Testland,TestProvider,192.0.2.1,"
    )
    assert content[2] == (
        "relay-002,relay-002-socks5,relay-002-socks5.relays.mullvad.net:1080,"
        "Test City,Testland,TestProvider,192.0.2.1,"
    )


def test_write_csv_handles_empty_relays(tmp_path: Path) -> None:
    destination = tmp_path / "empty.csv"

    write_csv([], destination)

    content = destination.read_text()
    assert content.strip() == (
        "hostname,socks5_hostname,socks5_endpoint,city,country,"
        "provider,ipv4,ipv6"
    )


def test_write_manifest_outputs_expected_payload(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"
    relays = [_relay("relay-001"), _relay("relay-002")]

    artifact_paths = {
        "json": tmp_path / "mullvad_relays.json",
        "text": tmp_path / "mullvad_relays.txt",
        "pac": tmp_path / "mullvad_relays.pac",
    }

    artifact_paths["json"].write_text("[]", encoding="utf-8")
    artifact_paths["text"].write_text("socks5://example", encoding="utf-8")
    artifact_paths["pac"].write_text("PAC", encoding="utf-8")

    write_manifest(
        relays,
        destination,
        filters={"countries": ["se"], "limit": 100},
        verification={"enabled": True, "limit": 5},
        artifacts={key: str(path) for key, path in artifact_paths.items()},
        metadata={"trigger": "manual", "run_id": "123"},
    )

    content = destination.read_text()
    data = json.loads(content)

    assert data["relay_count"] == 2
    assert data["filters"] == {"countries": ["se"], "limit": 100}
    assert data["verification"] == {"enabled": True, "limit": 5}
    json_artifact = data["artifacts"]["json"]
    assert json_artifact["path"] == str(artifact_paths["json"])
    assert json_artifact["sha256"] == hashlib.sha256(b"[]").hexdigest()
    assert data["metadata"]["trigger"] == "manual"
    assert "generated_at" in data
