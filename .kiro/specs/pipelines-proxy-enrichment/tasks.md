# Implementation Plan

- [x] 1. Establish multi-source relay aggregation foundation
- [x] 1.1 Reinforce source orchestration so Mullvad is always fetched first and uv-driven usage stays canonical
  - Ensure the CLI workflow documents `uv run python build_relay_list.py …` as the supported entry point for fetching and updating SOCKS5 relays
  - Confirm Mullvad remains the baseline source while adapters honor cache bypass directives and record timing diagnostics
  - _Requirements: 1.1, 1.4, 1.5_

- [x] 1.2 Add adapter-aware resilience and observability so partial source failures are surfaced without halting the entire pipeline
  - Retry supplemental sources once with measured delays, capturing attempts, errors, and cache flags for reporting
  - Continue processing remaining sources when an adapter fails while emitting structured logs for operators
  - _Requirements: 1.2, 1.3_

- [x] 2. Strengthen filtering and normalization behaviors
- [x] 2.1 Expand filtering logic to respect all country, city, ownership, and provider combinations while preserving default active/include rules
  - Apply inclusive filters only when specified, otherwise fall back to active and include_in_country defaults
  - Capture unmatched filter tokens and representative exclusions for user-facing warnings
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.2 Normalize relay metadata into deterministic SOCKS5 outputs that retain canonical geography and provider context
  - Derive SOCKS5 hostnames from source data and maintain stable ordering across repeated runs
  - Verify filtered relays remain sorted before optional limiting to guarantee deterministic artifacts
  - _Requirements: 2.4, 4.1, 4.3_

- [x] 3. Implement validation and enrichment pipeline
- [x] 3.1 Introduce a validation stage that rejects relays missing critical fields and halts on schema regressions with actionable errors
  - Check each relay for hostname, socks5 endpoint, provider, location identifiers, and IPv4 presence before enrichment
  - Escalate structural mismatches with explicit source identifiers to fail the run early when schemas drift
  - _Requirements: 3.1, 3.2_

- [x] 3.2 Enrich accepted relays with derived availability insights, provider classifications, and display labels required downstream
  - Attach computed attributes and run diagnostics that describe enrichment results for later reporting
  - Feed verification sampling preferences into enrichment outputs to support downstream stages
  - _Requirements: 3.3, 5.4_

- [x] 3.3 Integrate Proxy Scraper Checker support so external verdicts augment relay metadata when enabled
  - Invoke the checker via subprocess, merge latency and protocol health details into enrichment, and treat non-zero exits as actionable failures
  - Emit operator guidance when the checker binary or export data is absent instead of attempting inline downloads
  - _Requirements: 3.4, 3.5_

- [x] 3.4 Capture Mubeng handshake enrichment whenever requested to extend verification context inside the enrichment results
  - Confirm the Mubeng binary path before execution, produce installation guidance when missing, and attach structured handshake verdicts to relays
  - _Requirements: 3.6_

- [x] 4. Deliver deterministic artifact publication with Mubeng-friendly outputs
- [x] 4.1 Write JSON, text, and PAC artifacts from enriched relays while ensuring directory management and deterministic ordering
  - Create the output directory on demand, persist enriched data to all artifact formats, and uphold consistent ordering even when limits apply
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 4.2 Ensure the text artifact remains a bare `host:port` list compatible with Mubeng consumption
  - Validate that every line omits scheme prefixes while retaining socks5 endpoints so Mubeng auto-detects the transport
  - _Requirements: 4.5_

- [x] 4.3 Surface artifact generation metrics that summarize counts, elapsed time, and limit effects in verbose mode
  - Emit per-artifact counts and durations once serialization completes to inform operators and CI logs
  - _Requirements: 4.4, 6.1_

- [x] 4.4 Emit canonical JSON when requested so downstream tooling can derive additional formats
  - When `--emit-canonical-json` is set, persist validated-but-unenriched relays to `mullvad_relays_canonical.json`
  - _Requirements: 4.5_

- [x] 5. Provide comprehensive verification and observability tooling
- [x] 5.1 Execute Binance preflight checks before proxy probing and integrate the verification helper with configurable sample sizes
  - Reach out to REST and WebSocket endpoints to confirm availability, then dispatch proxy probes honoring requested sample limits
  - _Requirements: 5.1, 5.3_

- [x] 5.2 Propagate verification outcomes with clear failure diagnostics and Mubeng-style summaries
  - Flag unsuccessful probes with endpoint-specific context, highlighting default targets when they fail, and publish Mubeng summaries where applicable
  - _Requirements: 5.2, 3.6_

- [x] 5.3 Expand logging to cover every pipeline stage and append persistent run records when configured
  - Timestamp each stage transition in verbose mode and optionally persist structured summaries for historical auditing
  - _Requirements: 5.4, 5.5_

- [x] 6. Safeguard streamlined execution and recovery
- [x] 6.1 Track stage durations against the SLA and reuse caches within TTL boundaries when permitted
  - Measure each pipeline segment, compare against the ≤5s budget, and reuse cached payloads without violating freshness guarantees
  - _Requirements: 6.1, 6.2_

- [x] 6.2 Retry transient stage failures once and elevate categorized exit codes for CI consumption
  - Retry enrichment or similar transient failures a single time before surfacing errors, and standardize exit codes across success and failure paths
  - _Requirements: 6.3, 6.4_

- [x] 7. Expand automated verification coverage
- [x] 7.1 Extend unit tests to cover aggregation retries, filter diagnostics, validation rejection paths, enrichment metadata, canonical output, and Mubeng text formatting
  - Add deterministic fixtures that exercise multi-source aggregation, filter edge cases, validation outcomes, canonical writer, and text artifact formatting expectations
  - _Requirements: 1.2, 2.3, 3.1, 3.3, 4.5_

- [x] 7.2 Grow integration tests that drive the CLI through fetch, transform, enrichment, artifact writing (including canonical JSON), and verification scenarios
  - Simulate runs with cache bypass, Proxy Scraper Checker data, and verification failures to confirm reporting semantics
  - _Requirements: 1.4, 4.1, 4.5, 5.1, 5.2_

- [x] 7.3 Add performance and regression checks that validate SLA adherence and exit code classifications
  - Benchmark representative runs under cached conditions and assert exit codes align with success and failure categories
  - _Requirements: 6.1, 6.4_

- [x] 8. Update documentation to surface uv workflow, canonical JSON, and Mubeng consumption details
  - Refresh `README.md` and supporting guides to highlight the `uv run python build_relay_list.py …` invocation, explain the canonical artifact, and describe how the text artifact feeds Mubeng and similar tooling
  - _Requirements: 1.5, 4.5_
