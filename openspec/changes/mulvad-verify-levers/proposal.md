## Why

Tip `115837ee` (after [#3](https://github.com/tommy-ca/mulvad-relay-list/pull/3) soft-fail schedule SOCKS, CLOSED) still has **no** `openspec/` tree and no formal lever-first VERIFY contract for poteto arena/interrogate/swarm handoff. #3 fixed schedule soft-fail honesty in product code; residual Todd ask is OpenSpec for verification skills/tools + honesty bar (Timeout≠PASS; soft≠green; Mullvad overlay prerequisite) without reminting #3 or inventing LIVE_PASS from GHA. Self-hosted Mullvad runner stays out of scope unless Todd asks.

## What Changes

- **Wave-4 (this PR):** Bootstrap `openspec/config.yaml` with `schema: intent-driven` (+ project-local schema for validate) and mint propose-only change `mulvad-verify-levers`. No product verify soft-fail remint. No AGENTS/skill Apply edits in this PR.
- **Wave-5 Apply (HOLD until Todd/Horizon go):** AGENTS.md honesty for soft vs hard verify + tunnel prerequisite; optional thin `.agents/skills/verify-mulvad-proxies`; optional machine-scannable soft-fail marker; merge NEW capability into tip `openspec/specs/`; keep pytest green; **do not** remint #3 workflow soft-fail logic unless a proved falsifier appears.

## Capabilities

### New Capabilities

- `mulvad-verify-levers`: Honesty bar for SOCKS verify (Timeout/connect-fail ≠ PASS; schedule soft-fail MUST print `SOFT-FAIL` and MUST NOT invent green; dispatch/`verify=true` without soft-fail env remains hard-fail; Mullvad overlay `10.124.x` prerequisite documented); lever-first VERIFY citing `scripts/verify_proxies.py` and/or `uv run pytest` (tests/test_verify_proxies.py); refuse prose-only / invent LIVE_PASS; AGENTS (+ optional thin verify skill on Apply) describe soft vs hard + tunnel; poteto arena/interrogate/swarm cites pstack / gbp long-horizon-swarm (cite not clone); propose-only fence / Apply HOLD / no remint #3 / no self-hosted runner without Todd / dual orch forbidden / orch metadata out of product trees; OpenSpec intent-driven present at tip after Apply.

### Modified Capabilities

- _(none — greenfield OpenSpec tree; prefer ADDED under NEW capability only)_

## Impact

Wave-4: `openspec/` bootstrap + change folder only (no product code). Wave-5 (after Todd/Horizon go): docs/skill honesty under AGENTS / optional `.agents/skills/verify-mulvad-proxies`; tip merge of NEW capability; config already landed by this PR once merged. Does **not** remint closed #3 / `mulvad-proxy-pipeline-red`. Does **not** invent LIVE_PASS. Does **not** open self-hosted Mullvad without Todd. Dual orch forbidden (Horizon leaf apply; Drove tick/quota only).

## Non-goals

- Remint #3 soft-fail product logic / workflow unless proved falsifier
- Invent LIVE_PASS / fake SOCKS green from GHA timeouts
- Self-hosted Mullvad runner without Todd ask
- Dual orch ownership
- Orch metadata inside product trees (`mullvad/`, `scripts/` product logic, workflow soft-fail remint)
- Product apply in the propose PR
- Vendor full intent-driven skill trees in propose (schema only for validate)

## Probe Evidence Record

- Evidence label: `Static`
  - Query: Tip SHA and OpenSpec absence
  - Path: tip `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` worktree root / `openspec/` (absent at tip)
  - Command: `git rev-parse origin/main` → `115837eed55f874ae34cd8c1bfd1a5eba74f18cf`; confirm no `openspec/` on tip
  - Result summary: Tip = floor after #3 MERGED; no OpenSpec tree before this change
  - Conclusion: Bootstrap intent-driven + mint NEW capability required

- Evidence label: `Static`
  - Query: Schedule soft-fail honesty already on tip (#3)
  - Path: `scripts/verify_proxies.py` (~L196–220); README CI note; `docs/spec.md` SOCKS verify prerequisite
  - Result summary: `GITHUB_EVENT_NAME==schedule` or `MULVAD_VERIFY_SOFT_FAIL` → print `SOFT-FAIL:…` and exit 0; hard path returns 2; README/docs document `10.124.x` tunnel-only
  - Conclusion: Do **not** remint #3; OpenSpec records honesty bar + lever cites

- Evidence label: `Static`
  - Query: CI verify trigger modes
  - Path: `.github/workflows/proxy-pipeline.yml` resolve + Run verification probes
  - Result summary: schedule forces verify=true; workflow_dispatch verify=true opt-in; step runs `uv run python scripts/verify_proxies.py`; public `ubuntu-latest` cannot reach overlay
  - Conclusion: Soft schedule vs hard dispatch without soft-fail env remains the contract

- Evidence label: `Static`
  - Query: Lever surfaces for VERIFY
  - Path: `scripts/verify_proxies.py`, `tests/test_verify_proxies.py`, `AGENTS.md` verify CLI lines
  - Result summary: Script + pytest local SOCKS fixture exist; AGENTS documents CLI but no soft/hard modes or dedicated verify-* skill / poteto cite contract
  - Conclusion: Apply HOLD for AGENTS/skill honesty; propose MUST refuse prose-only VERIFY

- Evidence label: `Metadata`
  - Query: Closed #3 / self-hosted OOS / dual orch
  - Path: `/workspace/orchestrate/mulvad-verify-levers/BRIEF.md`, `WAVE-0-READY.md`
  - Result summary: Must-nots: no remint #3; no invent LIVE_PASS; dual orch forbidden; self-hosted Mullvad OOS; orch metadata out of product trees
  - Conclusion: Encode as ADDED requirements + tasks Band B HOLD
