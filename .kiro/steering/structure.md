# Project Structure

## Top-Level Layout
- `build_relay_list.py` — CLI entry point coordinating fetch → transform → validate → enrich → output pipeline stages.
- `mullvad/` — Core library modules (HTTP client, transforms, outputs, randomizer, domain errors).
- `scripts/` — Operational helpers such as `verify_proxies.py` for post-build validation.
- `tests/` — Pytest suite mirroring module layout with fixtures under `tests/data/`.
- `docs/` — Living specification (`docs/spec.md`) capturing product requirements and design decisions.
- `examples/` — Checked-in sample artifacts demonstrating expected output formats.
- `build/` — Generated artifacts (ignored by git) created during pipeline execution.
- `.claude/commands/kiro/` — Spec-driven command definitions powering the Kiro workflow.

## Core Modules
- `mullvad/api.py` — Fetches Mullvad relay metadata, manages optional caching, and raises `RelayBuildError` on failures.
- `mullvad/transform.py` — Houses filter/enrichment helpers (country/provider filters, ownership toggles, SOCKS5 derivations).
- `mullvad/output.py` — Serializes canonical relay list into JSON, text, and PAC formats.
- `mullvad/randomizer.py` — Provides deterministic random selection helpers (weighted/unweighted) for consumers.
- `mullvad/errors.py` — Centralizes domain-specific exceptions for consistent CLI error handling.

## CLI & Scripts
- `build_relay_list.py` orchestrates the pipeline using argparse flags:
  - Filtering knobs (`--countries`, `--providers-allow`, `--include-owned`, etc.).
  - Operational toggles (`--limit`, `--output-dir`, `--no-cache`, `--verbose`).
- `scripts/verify_proxies.py` loads generated JSON artifacts and probes selected proxies against HTTP/WS endpoints to validate connectivity.

## Testing Layout
- Unit tests mirror module names (`tests/test_transform.py`, `tests/test_output.py`, etc.) with deterministic fixtures in `tests/data/`.
- Verification tests exercise serialization formats and randomizer behavior.
- Follow repository guidelines: add new tests as `test_<module>.py`, favor parametrization and seeded randomness.

## Pipeline Flow
1. **Fetch** (`mullvad/api.py`) pulls fresh relay data (cached unless `--no-cache`).
2. **Transform** (`mullvad/transform.py`) filters and normalizes records according to CLI arguments.
3. **Validate/Enrich** ensures active relays only, derives SOCKS5 hostnames, and attaches metadata needed downstream.
4. **Output** (`mullvad/output.py`) writes artifacts to `build/` (or supplied directory) and logs summaries.
5. **Verify** (optional) uses `scripts/verify_proxies.py` to confirm sample endpoints respond.

## Naming & Conventions
- Python modules use `snake_case`; classes follow `PascalCase`; constants uppercase.
- Imports ordered stdlib → third-party → local.
- Generated artifacts live under `build/` (ignored) while curated samples belong in `examples/`.
- Keep new helpers deterministic and colocated with related functionality (`transform.py` for data reshaping, etc.).
