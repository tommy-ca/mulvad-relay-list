import json
import sys
from pathlib import Path

import pytest

import build_relay_list
from mullvad.errors import RelayBuildError
from mullvad.verifier import VerificationSummary
from scripts.verify_proxies import ProxyResult


@pytest.fixture(scope="module")
def sample_payload():
    data_path = Path(__file__).parent / "data" / "wireguard_sample.json"
    return json.loads(data_path.read_text())


def test_build_relay_list_end_to_end(monkeypatch, tmp_path, sample_payload, capsys):
    def fake_fetch(self, *, force_refresh: bool = False):
        return sample_payload

    monkeypatch.setattr("mullvad.api.MullvadAPI.fetch_wireguard_relays", fake_fetch)

    args = [
        "build_relay_list.py",
        "--output-dir",
        str(tmp_path),
        "--no-cache",
        "--verbose",
        "--emit-canonical-json",
    ]
    monkeypatch.setattr(sys, "argv", args)

    exit_code = build_relay_list.main()
    assert exit_code == 0

    json_path = tmp_path / "mullvad_relays.json"
    text_path = tmp_path / "mullvad_relays.txt"
    pac_path = tmp_path / "mullvad_relays.pac"
    canonical_path = tmp_path / "mullvad_relays_canonical.json"

    assert json_path.exists()
    assert text_path.exists()
    assert pac_path.exists()
    assert canonical_path.exists()

    relays = json.loads(json_path.read_text())
    assert len(relays) == 5
    assert all(relay["socks5_endpoint"].endswith(".relays.mullvad.net:1080") for relay in relays)

    text_lines = [line for line in text_path.read_text().splitlines() if line]
    assert text_lines == [entry["socks5_endpoint"] for entry in relays]

    canonical_payload = json.loads(canonical_path.read_text())
    assert len(canonical_payload) == len(relays)
    assert all("display_label" not in item for item in canonical_payload)
    assert canonical_payload[0]["socks5_endpoint"].endswith(".relays.mullvad.net:1080")

    pac_content = pac_path.read_text()
    assert "FindProxyForURL" in pac_content

    captured = capsys.readouterr()
    assert "Wrote 5 relays" in captured.out


def test_build_relay_list_with_verification(monkeypatch, tmp_path, sample_payload):
    def fake_fetch(self, *, force_refresh: bool = False):
        return sample_payload

    monkeypatch.setattr("mullvad.api.MullvadAPI.fetch_wireguard_relays", fake_fetch)

    proxy_endpoint = "al-tia-wg-socks5-003.relays.mullvad.net:1080"
    results = [
        ProxyResult(
            endpoint=proxy_endpoint,
            http_ok=True,
            http_error=None,
            http_origin="origin",
            ws_ok=True,
            ws_error=None,
        )
    ]
    summary = VerificationSummary(results=results)

    calls = {}

    def fake_preflight(*args, **kwargs):
        calls["preflight"] = True

    def fake_verify(endpoints, **kwargs):
        calls["verify"] = endpoints
        return summary

    def fake_run_mubeng(endpoints, **kwargs):
        calls["mubeng"] = list(endpoints)
        return {"ok": True, "checked": len(endpoints)}

    monkeypatch.setattr("build_relay_list.preflight_targets", fake_preflight)
    monkeypatch.setattr("build_relay_list.run_proxy_verification", fake_verify)
    monkeypatch.setattr("build_relay_list.run_mubeng", fake_run_mubeng)

    checker_script = tmp_path / "checker.py"
    checker_script.write_text(
        """#!/usr/bin/env python3
import json
import sys

endpoints = [line.strip() for line in sys.stdin if line.strip()]
payload = []
for endpoint in endpoints:
    payload.append({
        "proxy": f"socks5://{endpoint}",
        "status": "alive",
        "latency_ms": 37,
        "source": "psc",
    })
print(json.dumps(payload))
"""
    )
    checker_script.chmod(0o755)

    args = [
        "build_relay_list.py",
        "--output-dir",
        str(tmp_path),
        "--no-cache",
        "--verify-limit",
        "1",
        "--verify-mubeng",
        "--verify-http-url",
        "https://example.com/ping",
        "--verify-ws-url",
        "wss://example.com/socket",
        "--enable-proxy-checker",
        "--proxy-checker-bin",
        str(checker_script),
    ]
    monkeypatch.setattr(sys, "argv", args)

    exit_code = build_relay_list.main()
    assert exit_code == 0
    assert calls["preflight"] is True
    assert calls["verify"] == [proxy_endpoint]
    assert calls["mubeng"] == [proxy_endpoint]

    json_payload = json.loads((tmp_path / "mullvad_relays.json").read_text())
    assert json_payload[0]["display_label"].startswith("Tirana")
    assert json_payload[0]["proxy_checker"]["latency_ms"] == 37


def test_build_relay_list_verification_failure(monkeypatch, tmp_path, sample_payload):
    def fake_fetch(self, *, force_refresh: bool = False):
        return sample_payload

    monkeypatch.setattr("mullvad.api.MullvadAPI.fetch_wireguard_relays", fake_fetch)

    proxy_endpoint = "al-tia-wg-socks5-003.relays.mullvad.net:1080"
    results = [
        ProxyResult(
            endpoint=proxy_endpoint,
            http_ok=False,
            http_error="boom",
            http_origin=None,
            ws_ok=True,
            ws_error=None,
        )
    ]
    summary = VerificationSummary(results=results)

    monkeypatch.setattr("build_relay_list.preflight_targets", lambda *a, **kw: None)
    monkeypatch.setattr(
        "build_relay_list.run_proxy_verification", lambda endpoints, **kw: summary
    )

    args = [
        "build_relay_list.py",
        "--output-dir",
        str(tmp_path),
        "--no-cache",
        "--verify-limit",
        "1",
    ]
    monkeypatch.setattr(sys, "argv", args)

    with pytest.raises(RelayBuildError):
        build_relay_list.main()
