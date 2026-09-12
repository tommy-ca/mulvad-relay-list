## Context

Tip floor `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` (`115837ee`) — merge of #3 soft-fail schedule SOCKS (`mulvad-proxy-pipeline-red` CLOSED). Repo has Kiro under `.kiro/specs/` but **no** `openspec/`. Verify surface: `scripts/verify_proxies.py` (schedule/`MULVAD_VERIFY_SOFT_FAIL` → print `SOFT-FAIL`, exit 0; else exit 2 on failure). CI: `.github/workflows/proxy-pipeline.yml` runs verify on schedule and dispatch `verify=true`. Docs: README CI note + `docs/spec.md` overlay prerequisite. Tests: `tests/test_verify_proxies.py` (local fixtures). AGENTS.md lists verify CLI but lacks soft/hard + poteto lever contract. Cloud Agents unavailable → on-box propose.

## Goals / Non-Goals

**Goals:**

- Bootstrap OpenSpec `schema: intent-driven` (minimal config + project-local schema for validate; no full skill-tree vendor in propose).
- NEW capability `mulvad-verify-levers` covering honesty bar, lever-first VERIFY, skills/poteto cites, propose fence / must-nots, config-at-tip.
- Wave-4 propose-only; `openspec validate --strict` PASS; OpenSpec PR only.
- Wave-5 Apply HOLD: AGENTS (+ optional thin skill / machine-scannable soft-fail marker); pytest still green; no #3 remint unless falsifier.

**Non-Goals:**

- Remint #3 soft-fail product/workflow logic
- Invent LIVE_PASS / fake SOCKS green
- Self-hosted Mullvad runner without Todd
- Dual orch; orch metadata in product trees
- Vendor full intent-driven `.agents/skills/*` in propose
- Product AGENTS/skill edits in the propose PR

## Decisions

1. **Change id `mulvad-verify-levers`** — sole NEW Act-on; do not rename without Todd go.
2. **NEW capability only** — greenfield OpenSpec; tip has no prior `openspec/specs/`; prefer ADDED, not MODIFIED.
3. **Bootstrap schema project-local** — copy `intent-driven` under `openspec/schemas/` so validate works; `config.yaml` activates it; skip Step-6 skill install for propose (not required for validate).
4. **Cite #3, don't remint** — honesty bar requirements describe tip behaviour already landed; Apply does not reopen soft-fail unless proved falsifier.
5. **Lever-first VERIFY** — Brief/orch MUST name `scripts/verify_proxies.py` and/or `uv run pytest`; refuse prose-only.
6. **Poteto cite-not-clone** — pstack + gbp long-horizon-swarm / WORKFLOW cited for arena/interrogate/swarm; bodies stay upstream.
7. **No new durable ADR** — documentation/honesty + OpenSpec bootstrap; no major new architecture beyond tip #3.
8. **Propose-only Wave-4** — AGENTS/skill Apply and optional soft-fail marker = Band B HOLD.
9. **Orch ownership** — Horizon leaf apply; Drove tick/quota; dual orch forbidden.

## Risks / Trade-offs

- [Operators treat schedule soft-fail exit 0 as green] → Spec SHALL require `SOFT-FAIL` print + docs; AGENTS Apply reinforces.
- [Prose VERIFY invents LIVE_PASS] → Lever-first requirement + refuse scenario.
- [Temptation to remint #3 during Apply] → Explicit non-goal; falsifier bar; tasks Band B forbids remint unless proved.
- [Self-hosted Mullvad scope creep] → OOS unless Todd asks.
- [Schema without skills confuses Apply bots] → Design notes skills optional on Apply; validate does not need them.
- [Dual orch / orch metadata leak] → Spec + tasks must-nots; metadata under `/workspace/orchestrate/mulvad-verify-levers/`.

## Migration Plan

1. Worktree `docs/openspec-mulvad-verify-levers` from tip `115837ee`.
2. Bootstrap `openspec/config.yaml` + `openspec/schemas/intent-driven/`.
3. Mint change artefacts; `openspec validate mulvad-verify-levers --type change --strict` → PASS.
4. Commit `docs(openspec): propose mulvad-verify-levers`; push; gh pr create propose-only; do not merge as apply.
5. Wave-5 after Todd/Horizon go: AGENTS (+ optional skill/marker); merge capability to `openspec/specs/`; re-validate; archive.
6. No #3 remint. No self-hosted Mullvad. No LIVE invent.

## Open Questions

None that block propose. Exact wording of AGENTS soft/hard section and whether to add the thin skill vs AGENTS-only is Wave-5 author choice within the SHALL. Machine-scannable soft-fail marker format (stdout token already `SOFT-FAIL`) is optional Apply polish, not a #3 remint.
