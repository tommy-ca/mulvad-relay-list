---
name: verify-mulvad-proxies
description: >-
  Use when verifying Mullvad SOCKS/HTTP/WS proxy probes, interpreting CI
  schedule soft-fail vs hard-fail, or claiming VERIFY for mulvad-relay-list —
  lever-first; Timeout≠PASS; soft≠green.
---
# verify-mulvad-proxies

Thin skill — points at repo levers. Does not vendor fleet/pstack skill trees.

## Levers

```bash
uv run pytest
uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 5
```

Optional evidence under `/workspace/orchestrate/mulvad-verify-levers/evidence/`.

## Honesty bar

- Timeout / connect-fail ≠ PASS
- Soft-fail (`GITHUB_EVENT_NAME=schedule` or `MULVAD_VERIFY_SOFT_FAIL`): MUST print `SOFT-FAIL`; exit 0 is publish gate, **not** LIVE_PASS
- Hard-fail (dispatch verify / local without soft env): non-zero exit on failure
- Overlay prerequisite: `10.124.x` / tunnel-only; public GHA cannot reach SOCKS
- Local pytest fixture green ≠ GHA overlay green
- Do not remint #3 soft-fail logic without a proved falsifier
- Refuse prose-only VERIFY / invent LIVE_PASS

## Poteto cites (cite not clone)

- pstack (arena / interrogate)
- `tommy-ca/grok-build-plugins` long-horizon-swarm / tip `WORKFLOW.md`
