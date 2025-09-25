from mullvad.transform import Relay
from mullvad.validation import ValidationResult, ValidationIssue, validate_relays


def make_relay(**overrides):
    base = dict(
        hostname="relay-001",
        socks5_hostname="relay-001-socks5",
        socks5_endpoint="relay-001-socks5.relays.mullvad.net:1080",
        location_id="xx-city",
        city="Test City",
        country="Testland",
        provider="TestProvider",
        ipv4="192.0.2.1",
        ipv6=None,
        weight=10,
        owned=False,
        active=True,
        include_in_country=True,
        source="mullvad",
    )
    base.update(overrides)
    return Relay(**base)


def test_validate_relays_accepts_complete_records():
    relay = make_relay()
    result = validate_relays([relay])
    assert result.ok
    assert result.valid_relays == [relay]
    assert result.issues == []


def test_validate_relays_flags_missing_fields():
    relay = make_relay(hostname="", ipv4="")
    result = validate_relays([relay])
    assert not result.ok
    assert result.valid_relays == []
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.relay is relay
    assert "hostname" in issue.reason and "ipv4" in issue.reason
