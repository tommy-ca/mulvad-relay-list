# Technology Stack

## Architecture
- **CLI Orchestrator**: `build_relay_list.py` wires together fetch, transform, validation, enrichment, and output stages.
- **Core Modules**: `mullvad/api.py` (HTTP + caching), `mullvad/transform.py` (filters/enrichment), `mullvad/output.py` (writers), `mullvad/randomizer.py` (selection helpers), `mullvad/errors.py` (domain exceptions).
- **Verification Utilities**: `scripts/verify_proxies.py` exercises generated outputs against HTTP/WebSocket targets for preflight checks.
- **Artifacts**: JSON, line-delimited text, and PAC files under `build/` (ignored in VCS) plus curated examples under `examples/`.

## Runtime & Tooling
- **Language**: Python ≥3.10 managed with [`uv`](https://github.com/astral-sh/uv) for dependency isolation and execution.
- **Execution**: `uv run python build_relay_list.py` for builds; `uv run pytest` for tests.
- **Caching**: Local `.cache/` directory stores Mullvad API responses (≤5 min) unless `--no-cache` is passed.
- **Distribution**: No packaging yet; intended for source checkout or CI pipeline execution.

## Dependencies
- **Core**: `requests` (HTTP client), `websocket-client` and `python-socks` + `pysocks` (proxy verification helpers).
- **Dev/Test**: `pytest`, `websockets`, `trustme` (fixture CA generation).
- **System Assumptions**: Internet access to Mullvad endpoints; optional targets for verifier default to public Binance ping API.

## Data Flow & Integrations
1. Fetch `https://api.mullvad.net/public/relays/wireguard/v2` for WireGuard relay metadata.
2. Optionally merge any supplemental proxy feeds when extending the pipeline (placeholder seams exist in `transform.py`).
3. Transform & filter records according to CLI flags (countries, providers, ownership, limit, etc.).
4. Validate schema expectations and enforce `active`/`include_in_country` defaults.
5. Enrich with derived SOCKS5 hostnames, location labels, and metadata needed by output formats.
6. Emit artifacts and, if requested, verify sample proxies against target endpoints.

## Common Commands
- Environment bootstrap: `uv sync`
- Sample build: `uv run python build_relay_list.py --limit 20 --verbose`
- Fresh build without cache: `uv run python build_relay_list.py --no-cache --output-dir build`
- Tests: `uv run pytest`
- Proxy verification: `uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 5`

## Configuration & Environment
- No required environment variables today; CLI flags drive behavior.
- Network egress to Mullvad API (HTTPS) required; optional HTTP/WS targets configurable via verifier flags.
- Outputs default to `build/`; override with `--output-dir` when running inside CI workspaces.

## Observability & Quality Gates
- `--verbose` flag enables timestamped logging across pipeline stages.
- Verification script failures should block downstream publishing steps.
- Follow TDD: introduce failing pytest, implement minimal fix, refactor with suite passing before merging.

## Security Considerations
- Do not persist raw API payloads long term; `.cache/` is ephemeral and ignored by git.
- Handle CLI input sanitization (provider/country filters) to avoid malformed requests.
- Keep dependencies constrained via `pyproject.toml` and `uv.lock`; review upgrades for proxy behavior changes.
