# Mullvad Relay List Builder Specification

**Last updated:** September 25, 2025

## 1. Goal & Background
- Provide an automated way to assemble an up-to-date list of Mullvad SOCKS5 relays so that individual browser requests can pick a random proxy, following the workflow described by K4YT3X (https://k4yt3x.com/using-a-random-mullvad-socks5-proxy-for-each-browser-request/)
- Improve on the blog post by exposing configurable filters, output formats, and reproducible build steps suitable for automation pipelines.

## 2. Scope
- **In scope:**
  - Fetch relay metadata from Mullvad's public API endpoints.
  - Filter relays by availability and user-specified criteria (country, city, ownership, provider allow/block lists).
  - Generate deterministic artifact files (JSON, line-delimited text, and PAC) representing the filtered relays and a helper routine to select a random entry.
  - Expose a CLI entry point (`build_relay_list.py`) that supports integration in cron jobs or CI.
- **Out of scope:**
  - Establishing or validating Mullvad account credentials.
  - Managing browser proxy configuration; only produce the relay artifacts.
  - Latency monitoring or health-checking relays beyond the API-provided flags.

## 3. Functional Requirements
1. **Data ingestion & aggregation**
   - Pull fresh data from `https://api.mullvad.net/public/relays/wireguard/v2` through `MullvadAPI`, honouring on-disk caching unless `--no-cache` is supplied.
   - Orchestrate source fetches via `SourceManager`, collecting Mullvad as the baseline source and allowing future adapters to contribute additional payloads in a single run.
   - Tag relays with their origin and record per-source diagnostics (duration, attempts, cache bypass) for downstream logging.
2. **Filtering & diagnostics**
   - Default filter: include only relays with `active == true` and `include_in_country == true`.
   - CLI flags cover `--countries`, `--cities`, `--include-owned`, `--providers-allow`, `--providers-block`, and `--limit` to cap results after sorting.
   - Produce unmatched filter tokens and representative excluded samples so operators can understand why relays were removed when `--verbose` is enabled.
3. **Validation & enrichment**
   - Validate required fields (`hostname`, `socks5_endpoint`, `provider`, `location_id`, `ipv4`) and fail fast on schema regressions with actionable errors.
   - Enrich accepted relays with derived display labels, availability hints, and Proxy Scraper Checker verdicts by invoking the external binary (or reading a supplied export) via the `--enable-proxy-checker` suite of flags (`--proxy-checker-bin`, `--proxy-checker-arg`, `--proxy-checker-timeout`, `--proxy-checker-export`).
   - Surface guidance when the Proxy Scraper Checker binary is missing instead of attempting inline downloads, per security best practice.
4. **Output generation**
   - Write enriched, deterministically ordered artifacts: `mullvad_relays.json` (full metadata), `mullvad_relays.txt` (newline-delimited endpoints), and `mullvad_relays.pac` (PAC script embedding the relay list).
   - When `--emit-canonical-json` is supplied, produce `mullvad_relays_canonical.json` containing the validated but unenriched Mullvad relay records so downstream tooling can derive additional formats from a stable baseline.
   - Ensure the output directory exists (creating it if necessary) and respect `--limit` for all artifact formats.
5. **Verification & observability**
   - Optionally probe a configurable sample via Binance REST/WebSocket targets (`--verify-limit`, `--verify-http-url`, `--verify-ws-url`, `--verify-timeout`, `--verify-http-ca`, `--verify-http-insecure`).
   - Run Mubeng checks when `--verify-mubeng` is supplied, executing the external binary (`--mubeng-bin`, `--mubeng-arg`, `--mubeng-timeout`) and treating non-zero exits or failed verdicts as build failures with clear messaging.
   - Record stage timings, total runtime, and verification summaries; emit SLA breach warnings when execution exceeds 5 seconds and append JSON summaries to `--log-file` when provided.
6. **CLI UX**
   - `uv run python build_relay_list.py [options]` drives the end-to-end pipeline while logging timestamped stage transitions in verbose mode.
   - `--output-dir` defaults to `build/`; `--no-cache` bypasses cached source payloads; `--log-file` appends structured JSON lines with run metadata (sources, counts, durations, verification results, SLA status).

## 4. Non-Functional Requirements
- **Reliability:** Fail fast with clear exit codes/messages when the Mullvad API is unreachable (include HTTP status and URL in error).
- **Performance:** Complete within 5 seconds under normal network conditions for <1500 relays. Cache HTTP responses for up to 5 minutes in a local `.cache` folder unless `--no-cache` is set, and record stage timings plus total duration for SLA reporting.
- **Portability:** Target Python 3.10+ managed through `uv`; dependencies live in `pyproject.toml` and lock in `uv.lock` with `requests` as the sole third-party requirement.
- **Tooling:** Prefer `uv run` commands for the CLI (`uv run python build_relay_list.py`) and tests (`uv run pytest`) to keep local workflows and CI aligned.
- **Security:** Use HTTPS endpoints only; do not persist API responses longer than necessary; require operators to install external verification binaries (Proxy Scraper Checker, Mubeng) themselves and provide clear guidance instead of inline downloads.
- **Observability:** Log progress steps to stdout with timestamps when `--verbose` is supplied, emit stage durations, verification summaries, SLA breach warnings, and append JSON structured logs when `--log-file` is configured.
- **Maintainability:** Apply SOLID, KISS, DRY, and YAGNI principles; keep modules focused, avoid dead code, and use uv-managed dependencies only.
- **Testing discipline:** Favour fixture-driven tests over network mocks, keep deterministic seeds, and require a red → green → refactor TDD loop for each change.

## 5. Implementation Plan
1. **Project layout**
   - `build_relay_list.py`: CLI orchestrator.
   - `mullvad/api.py`: HTTP client with optional caching.
   - `mullvad/pipeline.py`: source orchestration helpers plus pipeline timing statistics.
   - `mullvad/transform.py`: filtering & joining helpers.
   - `mullvad/validation.py`: schema checks and validation result reporting.
   - `mullvad/enrich.py`: enrichment helpers that prepare display metadata and verification candidates.
   - `mullvad/proxy_checker.py`: Proxy Scraper Checker integration layer.
   - `mullvad/verifier.py`: Binance preflight, proxy verification, and Mubeng wrapper utilities.
   - `mullvad/output.py`: serializers for JSON/text/PAC.
   - `mullvad/randomizer.py`: random selection helper.
   - `tests/`: unit tests for filtering and random selection.
2. **Error handling**
   - Raise custom `RelayBuildError` for recoverable failures; surface message to CLI.
   - Validate user-provided filters (e.g., unknown country codes) with warnings but continue if possible.
   - Treat Proxy Scraper Checker and Mubeng subprocess failures as actionable errors, including timeout and missing-binary guidance.
3. **Testing strategy**
   - Drive all changes with pytest following a TDD cadence: write a failing test, make the minimal code change, then refactor with the suite green.
   - Use trimmed fixtures under `tests/data/`; prefer parametrized cases and deterministic seeds over mocks. Provide stub binaries for Proxy Scraper Checker and Mubeng interactions to keep tests hermetic.
   - Run `uv run pytest` plus a CLI smoke test against recorded data (no live network).
4. **Refactor workflow**
   - Start from the smallest vertical slice (fetch → filter → output) and expand iteratively.
   - Apply SOLID boundaries between modules, keep implementations simple (KISS), factor shared logic once (DRY), and skip speculative flags (YAGNI).
   - Maintain naming that matches existing `relay_*` and provider terminology; avoid legacy branches or compatibility shims and remove dead code quickly.
5. **Deliverables**
   - Source modules under `mullvad/`.
   - Executable script `build_relay_list.py` with arg parsing.
   - `pyproject.toml` and `uv.lock` for dependency management, `README.md` documenting the uv workflow, and `docs/spec.md` (this file).
   - Example output artifacts (JSON/TXT/PAC) checked into `examples/` for reference.

## 6. Open Questions & Assumptions
- Assume Mullvad's SOCKS relay endpoint remains unauthenticated and stable. Need to revisit if API schema changes.
- Weight field semantics: treat higher weights as more desirable when doing weighted selection (per Mullvad docs).
- IPv6 inclusion defaults to `None` if missing; outputs should gracefully handle absent fields.
- External verification tooling: assume operators install Proxy Scraper Checker (Rust) and Mubeng (Go) via `mise` or equivalent; pipeline should only verify presence and execute, never download binaries automatically.

## 7. Milestones
1. Scaffold project + caching HTTP client.
2. Implement data transform & filtering logic.
3. Implement output writers + CLI integration.
4. Add automated tests & example artifacts.
5. Document usage & deliver final review.
