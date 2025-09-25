import json
from pathlib import Path

import pytest

from mullvad.errors import RelayBuildError
from mullvad.pipeline import BaseSourceAdapter, SourceManager
from mullvad.transform import FilterConfig


class DummyMullvadAPI:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def fetch_wireguard_relays(self, *, force_refresh: bool = False):
        self.calls.append(force_refresh)
        return self.payload


class StubAdapter(BaseSourceAdapter):
    def __init__(self, name, responses):
        self._name = name
        self._responses = iter(responses)
        self.calls = []

    @property
    def name(self) -> str:
        return self._name

    def fetch(self, *, force_refresh: bool):
        self.calls.append(force_refresh)
        result = next(self._responses)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture(scope="module")
def mullvad_payload():
    sample_path = Path(__file__).parent / "data" / "wireguard_sample.json"
    return json.loads(sample_path.read_text())


@pytest.fixture
def manager_factory():
    def _factory(mullvad_payload, adapters=(), retry_delay=0.0):
        api = DummyMullvadAPI(mullvad_payload)
        manager = SourceManager(api_client=api, adapters=list(adapters), retry_delay=retry_delay)
        return api, manager

    return _factory


def test_source_manager_fetches_mullvad_payload(manager_factory):
    api, manager = manager_factory({"hello": "world"})
    results = manager.fetch_all()
    assert len(results) == 1
    result = results[0]
    assert result.name == "mullvad"
    assert result.payload == {"hello": "world"}
    assert result.attempts == 1
    assert result.error is None
    assert result.cache_bypassed is False
    assert api.calls == [False]


def test_source_manager_marks_cache_bypass_with_force_refresh(manager_factory):
    api, manager = manager_factory({"data": 1})
    results = manager.fetch_all(force_refresh=True)
    result = results[0]
    assert result.cache_bypassed is True
    assert api.calls == [True]


def test_source_manager_retries_transient_adapter_failure(manager_factory):
    adapter = StubAdapter(
        "flaky",
        responses=[RelayBuildError("boom"), {"ok": True}],
    )
    _, manager = manager_factory({"base": "payload"}, adapters=[adapter], retry_delay=0.0)
    results = manager.fetch_all()
    assert len(results) == 2
    mullvad, flaky = results
    assert mullvad.name == "mullvad"
    assert flaky.name == "flaky"
    assert flaky.payload == {"ok": True}
    assert flaky.error is None
    assert flaky.attempts == 2
    assert adapter.calls == [False, False]


def test_source_manager_records_failure_after_retry(manager_factory):
    adapter = StubAdapter(
        "broken",
        responses=[RelayBuildError("oops"), RelayBuildError("oops again")],
    )
    _, manager = manager_factory({"base": "payload"}, adapters=[adapter], retry_delay=0.0)
    results = manager.fetch_all()
    assert len(results) == 2
    broken = results[1]
    assert broken.name == "broken"
    assert broken.payload is None
    assert isinstance(broken.error, RelayBuildError)
    assert broken.attempts == 2
    assert adapter.calls == [False, False]


def test_source_manager_produces_unified_payload_list(mullvad_payload):
    api = DummyMullvadAPI(mullvad_payload)
    adapter = StubAdapter(
        "custom",
        responses=[{"wireguard": {"relays": []}, "locations": {}}],
    )
    manager = SourceManager(api_client=api, adapters=[adapter])
    results = manager.fetch_all()
    assert [result.name for result in results] == ["mullvad", "custom"]
    assert results[0].payload == mullvad_payload
    assert results[1].payload == {"wireguard": {"relays": []}, "locations": {}}
