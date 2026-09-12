# ADR Review Manifest

- Status: completed
- Review date: 2026-09-12

## Review Summary

ADR review completed for this change. **No new durable ADR.** Soft-fail schedule honesty is already landed by closed #3 on tip `115837ee`. This change bootstraps OpenSpec intent-driven and records verification-lever / honesty-bar behaviour as a NEW capability — documentation and orch contract, not a new long-lived architectural commitment. Prefer cite tip #3 + README/docs/spec overlay notes; do not mint a repo `adr/` that duplicates that product decision. No supersession graph (repo has no `adr/` folder at tip).

## In-Force ADRs Reviewed

- None under repo-root `adr/` (absent at tip floor `115837ee`).

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced.

## Arena / Act-on locks named

- Sole NEW Act-on id: **`mulvad-verify-levers`**
- Tip floor: `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` (`115837ee`) — #3 soft-fail CLOSED
- **Do not remint** #3 / `mulvad-proxy-pipeline-red`
- Self-hosted Mullvad runner **OOS** unless Todd asks
- Dual orch forbidden; Horizon leaf apply; Drove tick/quota only
- No invent LIVE_PASS / fake SOCKS green
- Orch metadata stays out of product trees
- Poteto arena/interrogate/swarm: cite pstack / gbp long-horizon-swarm — cite not clone
