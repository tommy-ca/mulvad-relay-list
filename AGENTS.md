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

## Coding Style & Naming Conventions
Use 4-space indentation, type hints, and dataclasses when they clarify payloads. Keep transforms in `transform.py`, deterministic helpers in `randomizer.py`, CLI glue in `build_relay_list.py`. Follow `snake_case` for functions, `PascalCase` for classes, uppercase for constants, and order imports stdlib → third-party → local. Keep docstrings tight and only comment on non-obvious logic.

## Testing Guidelines
Add pytest modules as `test_<module>.py`; store fixtures in `tests/data/`. Seed RNG helpers, prefer parametrized cases, and run `uv run pytest` before any push or PR.

## Commit & Pull Request Guidelines
Write imperative, scope-prefixed subjects (e.g., `transform: handle owned relays`) ≤72 characters, with optional detail in the body. Reference spec sections or tickets when behavior shifts. PR descriptions should list validation commands (build + `uv run pytest`), summarize artifact diffs, and include logs/screens when CLI output changes.

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
