# Requirements Document

## Introduction
Deliver a deterministic Mullvad SOCKS5 proxy pipeline that aggregates trusted relay sources, normalizes and enriches the data, validates reachability, and publishes reusable artifacts with verification telemetry so operations teams can automate proxy rotations confidently.

## Requirements

### Requirement 1: Source Aggregation
**Objective:** As an operations engineer, I want the pipeline to gather relay data from Mullvad and optional supplemental feeds so downstream filters start from a complete inventory.

#### Acceptance Criteria
1. WHEN the pipeline is invoked THEN the Proxy Pipeline SHALL fetch the Mullvad WireGuard relay feed over HTTPS before any downstream processing, treating it as the required SOCKS5 baseline.
2. WHEN additional relay sources are configured THEN the Proxy Pipeline SHALL retrieve each configured source within the same run and tag resulting records with the originating source identifier.
3. IF any source fetch fails THEN the Proxy Pipeline SHALL log the failure with status details and continue processing remaining sources unless every source fails.
4. IF `--no-cache` is provided THEN the Proxy Pipeline SHALL bypass local caches for every source and force live fetches while still recording fetch diagnostics.
5. WHEN operators follow repository instructions THEN the project documentation SHALL prescribe the canonical `uv run python build_relay_list.py ...` command for fetching and updating the SOCKS5 relay lists so execution stays aligned with the supported toolchain.

### Requirement 2: Filtering & Normalization
**Objective:** As a network automation engineer, I want configurable filters and normalized records so generated lists match routing policies without manual edits.

#### Acceptance Criteria
1. WHEN filters for countries, cities, ownership, or providers are supplied THEN the Proxy Pipeline SHALL exclude relays that do not satisfy every provided filter token.
2. WHEN no filters are provided THEN the Proxy Pipeline SHALL default to relays flagged as active and include_in_country by the source metadata.
3. IF a filter value does not match any known option THEN the Proxy Pipeline SHALL emit a warning and continue processing remaining relays.
4. WHEN normalization finishes THEN the Proxy Pipeline SHALL emit SOCKS5 hostnames derived from source records alongside canonical country, city, and provider metadata in deterministic order.

### Requirement 3: Validation & Enrichment
**Objective:** As a reliability engineer, I want the pipeline to validate schema integrity and enrich relay records so only trustworthy proxies advance to publication.

#### Acceptance Criteria
1. WHEN candidate relays are assembled THEN the Proxy Pipeline SHALL validate required fields (hostname, socks5 endpoint, provider, location identifiers, IPv4) and discard records missing critical data.
2. WHEN schema regressions are detected in any source payload THEN the Proxy Pipeline SHALL fail the run with actionable error details identifying the offending source and field.
3. WHEN enrichment executes THEN the Proxy Pipeline SHALL attach derived attributes such as availability flags, provider classifications, display labels, and run diagnostics required by outputs.
4. WHEN the Proxy Scraper Checker enricher is enabled THEN the Proxy Pipeline SHALL invoke the checker via subprocess, capture its JSON verdicts (latency, protocol health), merge results into relay metadata, and treat non-zero exits as enrichment failures with actionable messaging.
5. WHEN the Proxy Scraper Checker binary is unavailable THEN the Proxy Pipeline SHALL emit guidance instructing operators to install it externally via the documented mise command without attempting inline downloads.
6. WHEN Mubeng verification enrichment is requested THEN the Proxy Pipeline SHALL confirm the Mubeng binary path, emit installation guidance if missing, and capture structured handshake results for each tested relay.

### Requirement 4: Artifact Publication
**Objective:** As a consumer service owner, I want deterministic SOCKS5 relay artifacts so automation jobs can ingest proxy lists without manual steps.

#### Acceptance Criteria
1. WHEN outputs are generated THEN the Proxy Pipeline SHALL write JSON, text, and PAC artifacts containing SOCKS5 endpoints into the configured output directory using deterministic ordering across runs.
2. IF an output directory is missing THEN the Proxy Pipeline SHALL create it before writing artifacts.
3. WHEN `--limit N` is supplied THEN the Proxy Pipeline SHALL cap each artifact to the first N validated relays after enrichment while maintaining deterministic ordering.
4. WHEN artifact-generation succeeds THEN the Proxy Pipeline SHALL surface summary metrics including counts per output and elapsed duration when `--verbose` is set.
5. WHEN canonical JSON output is requested THEN the Proxy Pipeline SHALL write `mullvad_relays_canonical.json` containing validated-but-unenriched relay data so downstream formats can be derived from the canonical source.

### Requirement 5: Verification & Observability
**Objective:** As a platform engineer, I want verification tooling and clear telemetry so I can trust the Mullvad-derived SOCKS5 proxy lists before release.

#### Acceptance Criteria
1. WHEN verification is requested THEN the Proxy Pipeline SHALL invoke the proxy verification helper to probe a configurable sample of generated relays against HTTP and optional WebSocket endpoints, defaulting to Binance REST `https://api.binance.com/api/v3/ping` and WebSocket `wss://stream.binance.com:9443/ws`.
2. IF any verification probe fails THEN the Proxy Pipeline SHALL mark the run unsuccessful, emit failing relay details, and highlight which target endpoint failed when defaults are used.
3. WHEN Binance defaults are selected THEN the Proxy Pipeline SHALL perform a pre-flight check confirming the Binance REST and WebSocket endpoints are reachable before exercising proxies.
4. WHEN verbose logging is enabled THEN the Proxy Pipeline SHALL log stage transitions (fetch, transform, validate, enrich, output, verify) with timestamps and counts for observability.
5. WHERE persistent logs are configured THEN the Proxy Pipeline SHALL append structured entries summarizing run outcomes and verification verdicts for later inspection.

### Requirement 6: Streamlined Execution
**Objective:** As a DevOps engineer, I want the pipeline to complete efficiently and recover gracefully so scheduled proxy updates stay within operational SLAs.

#### Acceptance Criteria
1. WHEN the pipeline completes a run THEN the Proxy Pipeline SHALL finish within the defined performance budget (≤5 seconds for current data volumes) or emit an alert when the budget is exceeded.
2. WHEN caching is permitted THEN the Proxy Pipeline SHALL reuse cached source payloads respecting TTL boundaries to minimize redundant network calls.
3. IF a transient stage error such as enrichment failure occurs THEN the Proxy Pipeline SHALL retry the failed stage once before surfacing the error.
4. WHEN the pipeline exits THEN the Proxy Pipeline SHALL emit explicit exit codes (0 success, non-zero categorized failures) suitable for CI integration.

