from mullvad.randomizer import pick_random
from mullvad.transform import Relay


class DummyRandom:
    def __init__(self):
        self.choices_args = None
        self.randrange_called = False

    def choices(self, population, weights=None, k=1):
        self.choices_args = (population, list(weights) if weights else None, k)
        return [population[-1]]

    def randrange(self, stop):
        self.randrange_called = True
        return 0


def _make_relay(hostname: str, weight: int) -> Relay:
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
        weight=weight,
        owned=False,
        active=True,
        include_in_country=True,
    )


def test_pick_random_weighted_uses_weights():
    relays = [_make_relay("relay-low", 1), _make_relay("relay-high", 100)]
    rng = DummyRandom()
    chosen = pick_random(relays, weighted=True, rng=rng)
    assert chosen == relays[-1]
    population, weights, k = rng.choices_args
    assert population == relays
    assert weights == [1, 100]
    assert k == 1


def test_pick_random_unweighted_uses_randrange():
    relays = [_make_relay("relay-low", 1), _make_relay("relay-high", 100)]
    rng = DummyRandom()
    chosen = pick_random(relays, weighted=False, rng=rng)
    assert chosen == relays[0]
    assert rng.randrange_called
