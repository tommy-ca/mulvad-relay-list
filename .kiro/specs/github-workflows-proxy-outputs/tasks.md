# Implementation Plan

- [ ] 1. Deliver multi-format relay artifacts
- [x] 1.1 Build CSV export capability
  - Define a deterministic column order covering hostnames, endpoints, locations, and provider metadata so every export presents uniform structure.
  - Generate CSV content directly from the enriched relay collection used for other formats to guarantee a single source snapshot.
  - Preserve stable delimiters and line endings so downstream automation ingests the file without post-processing.
  - _Requirements: R2.1_

- [x] 1.2 Produce manifest metadata for each run
  - Capture relay counts, applied filters, verification flags, and runtime timestamps in a machine-readable summary document.
  - Associate artifact file names and hashes with the manifest to support publication integrity checks.
  - Expose manifest content for later publication so consumers can audit how lists were produced.
  - _Requirements: R2.1, R3.1_

- [ ] 2. Configure pipeline automation workflow
- [x] 2.1 Implement scheduled pipeline execution
  - Register an hourly schedule that triggers the workflow at the start of each hour without manual intervention.
  - Prepare environment bootstrap steps that install dependencies and hydrate cache directories before running the pipeline.
  - Ensure the scheduled run applies production-oriented flags, including cache bypass and verbose logging.
  - _Requirements: R1.1_

- [x] 2.2 Expose manual dispatch controls
  - Add workflow inputs that accept filter overrides, verification toggles, and canonical export preferences from maintainers.
  - Translate workflow inputs into pipeline arguments at runtime while documenting chosen values in logs.
  - Provide defaults so dispatches operate safely when optional inputs are omitted.
  - _Requirements: R1.2, R4.1_

- [x] 2.3 Enforce single-run concurrency
  - Group workflow executions under a shared concurrency key to queue overlapping triggers.
  - Surface clear log messages when a run defers because another invocation is still active.
  - Confirm queued executions resume automatically after the active run completes to prevent artifact contention.
  - _Requirements: R1.3_

- [ ] 3. Publish artifacts for main branch consumers
- [x] 3.1 Upload workflow artifacts with retention
  - Collect JSON, CSV, text, PAC, and manifest outputs into discrete artifacts at the end of each run.
  - Configure artifact retention for at least seven days so teams can retrieve historical runs.
  - Fail the job when an upload does not succeed and include the failure message in the workflow summary.
  - _Requirements: R3.1, R3.3_

- [x] 3.2 Push outputs to publication branch
  - Retrieve artifact bundle after a successful main-branch run and project files into a clean publication workspace.
  - Commit the latest artifacts to a dedicated branch using automation credentials while guarding against missing tokens.
  - Announce raw file URLs and commit identifiers in the publication step summary for downstream consumption.
  - _Requirements: R3.2, R3.3, R4.3_

- [x] 3.3 Maintain hourly release tag
  - Create or update a `hourly-latest` GitHub release that points to the publication branch tip after each successful run.
  - Populate release notes with links to the originating workflow run and artifact bundle URLs.
  - Fail the workflow when the release API call does not succeed so operators can intervene.
  - _Requirements: R3.2_

- [ ] 4. Strengthen observability and guardrails
- [x] 4.1 Enhance run logging and summaries
  - Emit grouped logs around fetch, transform, verification, and publication stages with precise timestamps.
  - Append a structured summary to the workflow run that highlights relay totals, filter inputs, and verification outcomes.
  - Share manifest and artifact links within the summary so auditors can trace outputs quickly.
  - _Requirements: R4.1, R4.3_

- [x] 4.2 Validate required secrets before execution
  - Detect absent publication credentials early and stop the workflow before the pipeline begins.
  - Record which secret check failed to give maintainers actionable remediation steps.
  - Prevent downstream jobs from running when guardrails fail, preserving consistent artifact states.
  - _Requirements: R4.2, R3.3_

- [ ] 5. Validate verification coverage and tests
- [x] 5.1 Integrate optional verification switch
  - Respect workflow input flags that enable or skip proxy verification during manual runs and scheduled executions.
  - Run lightweight verification samples by default for scheduled runs to maintain reasonable duration.
  - Halt the workflow and surface detailed verifier output when any sampled proxy fails checks.
  - _Requirements: R2.2, R2.3, R4.1_

- [ ] 5.2 Add regression tests for new exporters
  - Cover CSV export behavior with unit tests that assert column ordering, encoding, and empty result handling.
  - Include manifest generation tests that validate recorded metadata and schema stability.
  - Seed tests to ensure deterministic outputs regardless of relay ordering.
  - _Requirements: R2.1, R3.1_

- [ ] 5.3 Exercise workflow paths before enabling schedule
  - Execute dry runs of the workflow via dispatch in a non-production branch to confirm job wiring.
  - Validate publication job behavior using a temporary target branch to avoid overwriting real artifacts.
  - Capture logs and summaries from rehearsal runs as evidence before turning on the cron schedule.
  - _Requirements: R1.1, R3.2, R4.1_
