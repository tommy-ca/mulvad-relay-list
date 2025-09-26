# Requirements Document

## Introduction
Automate Mullvad relay proxy pipeline executions via GitHub Actions so scheduled and on-demand runs generate auditable proxy lists in multiple formats and deliver them to downstream consumers without manual steps.

## Requirements

### Requirement 1: Workflow Orchestration
**Objective:** As a platform engineer, I want GitHub Actions to orchestrate scheduled and manual proxy pipeline runs so relays stay current without human babysitting.

#### Acceptance Criteria
1. WHEN the hourly cron schedule at the top of the hour triggers THEN GitHub Actions automation SHALL execute the Mullvad relay pipeline with the production configuration.
2. WHEN a maintainer manually dispatches the workflow on the `main` branch THEN GitHub Actions automation SHALL accept optional inputs for relay filters and execute the pipeline with those overrides.
3. IF a workflow run is already in progress WHEN another trigger fires THEN GitHub Actions automation SHALL defer the new run until the active run completes to avoid conflicting artifact writes.

### Requirement 2: Multi-Format Artifact Generation
**Objective:** As a downstream automation integrator, I want consistent relay lists in multiple formats so infrastructure jobs can consume the data without custom conversions.

#### Acceptance Criteria
1. WHEN the pipeline workflow completes its data processing THEN GitHub Actions automation SHALL produce JSON, CSV, and plain-text relay lists derived from the same source snapshot.
2. IF verification is enabled via workflow inputs THEN GitHub Actions automation SHALL run `uv run python scripts/verify_proxies.py` against the generated JSON artifact before publishing results.
3. WHEN verification fails for any sampled proxy THEN GitHub Actions automation SHALL mark the workflow run as failed and attach the verifier output to the job summary.

### Requirement 3: Distribution and Retention
**Objective:** As a release engineer, I want generated proxy artifacts to be reliably accessible so consumers can retrieve the latest lists from a predictable location.

#### Acceptance Criteria
1. WHEN a workflow run completes successfully on any branch THEN GitHub Actions automation SHALL upload the generated artifacts to the run with a minimum seven-day retention policy.
2. WHEN the hourly workflow succeeds on the `main` branch THEN GitHub Actions automation SHALL publish the artifacts to a dedicated output branch that exposes raw files via HTTPS for external consumers and create/update a GitHub release tagged `hourly-latest`.
3. THEN the release notes SHALL include an entry linking back to the originating workflow run using the artifact bundle URL emitted by `proxy-pipeline`.
4. IF artifact upload, branch publication, or release creation fails at any step THEN GitHub Actions automation SHALL fail the workflow and emit actionable error logs in the summary.

### Requirement 4: Observability and Guardrails
**Objective:** As an operations analyst, I want clear visibility into workflow executions so issues surface quickly and can be triaged.

#### Acceptance Criteria
1. WHEN the workflow executes each major stage THEN GitHub Actions automation SHALL emit timestamped logs summarizing fetch, transform, verification, and publishing outcomes.
2. IF required secrets or tokens are missing at runtime THEN GitHub Actions automation SHALL halt before executing the pipeline and record which secret gate failed.
3. WHEN a workflow completes successfully THEN GitHub Actions automation SHALL post a concise success summary including artifact links in the run output for auditing purposes.
