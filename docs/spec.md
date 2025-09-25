# Mullvad Relay List Builder Specification

**Last updated:** September 24, 2025

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
1. **Data ingestion**
   - Pull fresh data from `https://api.mullvad.net/public/relays/wireguard/v2`.
   - Derive SOCKS5 relay hostnames by replacing the `wg-` segment of each relay hostname with `wg-socks5-`, appending `.relays.mullvad.net:1080`, per Mullvad naming conventions in the reference article.
   - Attach readable city/country metadata using the response `locations` dictionary.
2. **Filtering**
   - Default filter: include only relays marked `active == true` and `include_in_country == true`.
   - CLI flags for `--countries`, `--cities`, `--include-owned`, `--providers-allow`, `--providers-block` (comma-separated).
   - Allow `--limit N` to cap the number of relays in the output after filtering.
3. **Output generation**
   - Write `build/mullvad_relays.json`: array of objects containing hostname, location, city, country, ipv4, ipv6, weight, provider, owned.
   - Write `build/mullvad_relays.txt`: newline-delimited list of `hostname|city|country|ipv4` for simple consumption.
   - Write `build/mullvad_relays.pac`: PAC script that embeds the SOCKS5 endpoints list and returns a random proxy via `FindProxyForURL`.
   - Provide a utility module exposing `pick_random(relays, weighted=True)` for consumers needing in-process randomization.
4. **CLI UX**
   - `uv run python build_relay_list.py [options]` fetches, filters, writes artifacts, and logs counts.
   - `--output-dir` flag defaults to `build/`.
   - `--no-cache` to bypass any cached responses (see Non-functional).

## 4. Non-Functional Requirements
- **Reliability:** Fail fast with clear exit codes/messages when the Mullvad API is unreachable (include HTTP status and URL in error).
- **Performance:** Complete within 5 seconds under normal network conditions for <1500 relays. Cache HTTP responses for up to 5 minutes in a local `.cache` folder unless `--no-cache` is set.
- **Portability:** Target Python 3.10+ managed through `uv`; dependencies live in `pyproject.toml` and lock in `uv.lock` with `requests` as the sole third-party requirement.
- **Tooling:** Prefer `uv run` commands for the CLI (`uv run python build_relay_list.py`) and tests (`uv run pytest`) to keep local workflows and CI aligned.
- **Security:** Use HTTPS endpoints only; do not persist API responses longer than necessary.
- **Observability:** Log progress steps to stdout with timestamps when `--verbose` is supplied.
- **Maintainability:** Apply SOLID, KISS, DRY, and YAGNI principles; keep modules focused, avoid dead code, and use uv-managed dependencies only.
- **Testing discipline:** Favour fixture-driven tests over network mocks, keep deterministic seeds, and require a red → green → refactor TDD loop for each change.

## 5. Implementation Plan
1. **Project layout**
   - `build_relay_list.py`: CLI orchestrator.
   - `mullvad/api.py`: HTTP client with optional caching.
   - `mullvad/transform.py`: filtering & joining helpers.
   - `mullvad/output.py`: serializers for JSON/text/PAC.
   - `mullvad/randomizer.py`: random selection helper.
   - `tests/`: unit tests for filtering and random selection.
2. **Error handling**
   - Raise custom `RelayBuildError` for recoverable failures; surface message to CLI.
   - Validate user-provided filters (e.g., unknown country codes) with warnings but continue if possible.
3. **Testing strategy**
   - Drive all changes with pytest following a TDD cadence: write a failing test, make the minimal code change, then refactor with the suite green.
   - Use trimmed fixtures under `tests/data/`; prefer parametrized cases and deterministic seeds over mocks.
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

## 7. Milestones
1. Scaffold project + caching HTTP client.
2. Implement data transform & filtering logic.
3. Implement output writers + CLI integration.
4. Add automated tests & example artifacts.
5. Document usage & deliver final review.
