# Tasks: mulvad-verify-levers

> Schema: intent-driven. Propose atoms → offline validate → **STOP** → Todd/Horizon-go apply → archive.
> Tip floor: `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` (`115837ee`). No auto-apply. No remint #3. No invent LIVE_PASS. No self-hosted Mullvad without Todd. Dual orch forbidden. Orch metadata out of product trees.

## 0. Preconditions (read-only) — serial gate

- [x] 0.1 Tip SHA Probe: `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` (≥ floor `115837ee`) — #3 soft-fail MERGED / CLOSED
- [x] 0.2 Re-read BRIEF + WAVE-0-READY; tip surfaces: README CI note, `scripts/verify_proxies.py` soft_fail, AGENTS verify CLI, workflow verify steps, `tests/test_verify_proxies.py`
- [x] 0.3 Parks held: remint #3 OUT; invent LIVE_PASS OUT; self-hosted Mullvad OUT; dual orch OUT; orch metadata in product trees OUT
- [x] 0.4 Confirm locked Act-on id `mulvad-verify-levers`; Cloud Agents unavailable → on-box worktree propose

## Parallel band A — Propose atoms (Wave-4) — P-parallel

Depends: §0

- [x] A.1 Bootstrap `openspec/config.yaml` (`schema: intent-driven`) + project-local `openspec/schemas/intent-driven/` (no full skill trees) — **P-parallel**
- [x] A.2 `proposal.md` — Why/What/Capabilities/Impact; Probe Evidence; non-goals — **P-parallel**
- [x] A.3 `specs/mulvad-verify-levers/spec.md` — ADDED honesty bar, lever-first VERIFY, skills/poteto cites, propose fence, config-at-tip — **P-parallel**
- [x] A.4 `design.md` — bootstrap; cite-not-remint #3; Apply HOLD — **P-parallel**
- [x] A.5 `adr.md` + `.openspec.yaml` — no new durable ADR; schema intent-driven — **P-parallel**

## 1. Validate --strict (offline) — serial gate

Depends: Parallel band A complete

- [x] 1.1 `openspec validate mulvad-verify-levers --type change --strict` (from worktree) → PASS
- [x] 1.2 Probe honesty: no product soft-fail remint in propose tree; levers named; no LIVE invent; no self-hosted ask
- [x] 1.3 Confirm Must-nots: no auto-apply; dual orch forbidden; Horizon leaf; Drove tick/quota only

## 2. STOP handoff — serial gate

Depends: §1 green

- [x] 2.1 Hand Horizon `openspec/changes/mulvad-verify-levers/` (+ orch VALID/BRIEF)
- [x] 2.2 Ledger: Wave-4 VALID propose-only; Apply HOLD until Todd/Horizon go
- [x] 2.3 **STOP** — no `openspec apply`; no AGENTS/skill product edit from propose executor; do not merge as apply; do not remint #3

## Parallel band B — Apply (Wave-5; Todd/Horizon go) — APPLY GO

Depends: Todd/Horizon go + §1 green

- [x] B.1 Update `AGENTS.md` verify section: soft vs hard modes + Mullvad tunnel/overlay prerequisite + named levers (`scripts/verify_proxies.py`, `uv run pytest`) — **P-parallel**
- [x] B.2 Optional: thin `.agents/skills/verify-mulvad-proxies` pointing at same levers + honesty bar (cite not clone fleet skills) — **P-parallel**
- [x] B.3 Optional: machine-scannable soft-fail marker polish if needed (tip already prints `SOFT-FAIL`) — **do not remint #3 workflow soft-fail logic unless proved falsifier**
- [x] B.4 Confirm `uv run pytest` still green; no invent LIVE_PASS from GHA
- [x] B.5 Merge capability delta into tip `openspec/specs/mulvad-verify-levers/`; keep `openspec/config.yaml` intent-driven
- [x] B.6 `openspec validate mulvad-verify-levers --type change --strict` (and `--all --strict` as needed) green after merge
- [x] B.7 Poteto handoff docs/cites: arena/interrogate/swarm → pstack + gbp long-horizon-swarm / WORKFLOW (cite not clone)
- [x] B.8 **Prove bars Static/Metadata/Runtime (claim VERIFIED only if all hold):**
  - [x] P1 tip has `openspec/config.yaml` with `schema: intent-driven`
  - [x] P2 AGENTS (and optional skill) describe soft vs hard + overlay prerequisite
  - [x] P3 lever-first VERIFY cites script and/or pytest; no prose-only LIVE_PASS
  - [x] P4 schedule soft-fail still prints `SOFT-FAIL`; dispatch hard without soft env; no #3 remint unless falsifier
  - [x] P5 tip ≥ `115837ee`; dual orch not violated; no self-hosted Mullvad without Todd
  - [x] NOT predicates: remint #3; invent LIVE_PASS; dual orch; propose PR claimed as apply

## 3. Archive — serial gate

Depends: Parallel band B complete + implementation on integration branch

- [x] 3.1 `openspec validate mulvad-verify-levers --type change --strict` still green before archive
- [x] 3.2 Archive per openspec-git-discipline (from integration after merge)
- [x] 3.3 Update ledger; reaffirm parks; note Prove status (VERIFIED only if Prove bars held — never invent)
