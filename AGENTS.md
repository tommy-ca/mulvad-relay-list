# Repository Guidelines

## Project Structure & Module Organization
`build_relay_list.py` drives the fetch → filter → write CLI. Core code sits in `mullvad/`: `api.py` (HTTP/cache), `transform.py` (filters), `output.py` (writers), `randomizer.py` (selection), `errors.py` (exceptions). Tests mirror this layout under `tests/`. Generated artifacts belong in ignored `build/`; committed samples live in `examples/`. Update `docs/spec.md` whenever behavior changes.

## Build, Test, and Development Commands
```bash
uv sync
uv run python build_relay_list.py --limit 20 --verbose         # sample build
uv run python build_relay_list.py --no-cache --output-dir build # fresh build
uv run pytest                                                   # unit tests
uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 5
```
Use `--http-url`/`--ws-url` to aim the verifier at custom targets (e.g., Binance `https://api.binance.com/api/v3/ping`).

## Proxy verify levers (honesty bar)

Named levers only — refuse prose-only LIVE_PASS / invent green from timeouts:

```bash
uv run pytest                                              # fixtures; ≠ GHA overlay reachability
uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 5
```

**Modes**

| Mode | When | On probe fail |
|------|------|----------------|
| Soft-fail | `GITHUB_EVENT_NAME=schedule` or `MULVAD_VERIFY_SOFT_FAIL` truthy | Prints `SOFT-FAIL:…` (overlay/tunnel); exit 0 so publish can proceed — **not** probe success |
| Hard-fail | Dispatch/`verify=true` or local without soft env | Non-zero exit (tip: 2); Timeout/connect-fail ≠ PASS |

**Prerequisite:** Mullvad SOCKS overlays resolve to RFC1918 `10.124.x` (or in-tunnel `10.64.0.1`) — reachable only on a Mullvad WireGuard tunnel. Public GitHub Actions cannot probe them. Tip ≥ `115837ee` (#3) already implements schedule soft-fail; do not remint unless a proved falsifier.

Thin skill: `.agents/skills/verify-mulvad-proxies`. Poteto arena/interrogate/swarm: **cite** pstack + `tommy-ca/grok-build-plugins` long-horizon-swarm / `WORKFLOW.md` — cite not clone.

## Coding Style & Naming Conventions
Use 4-space indentation, type hints, and dataclasses when they clarify payloads. Keep transforms in `transform.py`, deterministic helpers in `randomizer.py`, CLI glue in `build_relay_list.py`. Follow `snake_case` for functions, `PascalCase` for classes, uppercase for constants, and order imports stdlib → third-party → local. Keep docstrings tight and only comment on non-obvious logic.

## Testing Guidelines
Add pytest modules as `test_<module>.py`; store fixtures in `tests/data/`. Seed RNG helpers, prefer parametrized cases, and run `uv run pytest` before any push or PR.

## Commit & Pull Request Guidelines
Follow Conventional Commits: `type(scope): imperative summary` ≤72 characters (e.g., `feat(pipeline): add proxy checker subprocess support`). Valid types include `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `chore`, and `perf`; use scopes that match repository modules (e.g., `transform`, `verifier`, `docs`). Reference spec sections or tickets when behavior shifts. PR descriptions should list validation commands (build + `uv run pytest`), summarize artifact diffs, and include logs/screens when CLI output changes.

## Semantic Log
Maintain a semantic log entry for every merged change in `docs/semantic-log.md` using the format `YYYY-MM-DD | type | scope | summary | validation`. Align the `type` column with Conventional Commit types, keep `scope` consistent with module names, and capture the exact validation command(s) executed. This log feeds release notes, so ensure each entry clearly communicates the user-visible impact.

## Security & Configuration Tips
Keep `build/`, `.cache/`, and raw API dumps out of version control; clean them before sharing. Use `--no-cache` for release verification. Document new env vars or dependencies in both `README.md` and this guide.

## Engineering Best Practices
- **SOLID:** One responsibility per module; inject dependencies instead of hard-coding.
- **KISS:** Choose clear filters and serializers over clever tricks.
- **DRY:** Centralize parsing/filter helpers in `mullvad/transform.py`; reuse CLI wiring.
- **YAGNI:** Add flags or outputs only for real requirements.
- **NO MOCKS:** Prefer recorded fixtures and seams over network mocks.
- **NO LEGACY:** Delete obsolete flags/configs instead of maintaining both paths.
- **NO COMPATIBILITY:** Target Python 3.10 via uv; drop shims for older runtimes.
- **CONSISTENT NAMING:** Match existing `relay_*` patterns and provider terminology.
- **START SMALL:** Ship thin slices before expanding scope.
- **TDD:** Write a failing pytest, implement the fix, refactor with the suite green.

## Kiro Spec-Driven Commands
Slash commands in `.claude/commands/kiro/` power the spec-driven workflow described in `CLAUDE.md`. Invoke them through the configured agent in order to keep specs, designs, and tasks synchronized.

### Steering & Context
- `/kiro:steering`: Audits the project state and refreshes steering docs under `.kiro/steering/` with current product, tech, and structure guidance.
- `/kiro:steering-custom <name>`: Adds or updates targeted steering files for specialized domains (e.g., security, APIs) so they can be pulled into future spec runs.

### Specification Lifecycle
- `/kiro:spec-init <project description>`: Creates a unique spec folder, seeds `spec.json`, and writes a stub `requirements.md` while updating `CLAUDE.md`'s active list.
- `/kiro:spec-requirements <feature-name>`: Generates EARS-formatted requirements from the spec description and marks the metadata with `requirements.generated=true`.
- `/kiro:spec-design <feature-name> [-y]`: Produces or refreshes the technical design, enforcing approved requirements unless `-y` auto-approves them; handles overwrite/merge flows for existing designs.
- `/kiro:spec-tasks <feature-name> [-y]`: Builds hierarchical implementation checklists that map back to requirements, auto-approving prior phases when invoked with `-y`.
- `/kiro:spec-impl <feature-name> [task-numbers]`: Drives TDD execution using the generated tasks, updating checkboxes as work completes.
- `/kiro:spec-status <feature-name>`: Reports the current phase, approval state, and outstanding work for the selected spec.

### Validation & Analysis
- `/kiro:validate-design <feature-name>`: Reviews the design for coverage, risks, and alignment with steering guidance before work begins.
- `/kiro:validate-gap <feature-name>`: Compares requirements against the existing codebase to highlight implementation gaps or areas needing refactor.
