# mulvad-verify-levers

Living capability after Wave-5 Apply. Tip floor ≥ `115837ee` (#3 soft-fail CLOSED).

## Requirements


### Requirement: Honesty bar for SOCKS verify outcomes

Feature: mulvad-verify-levers
Rule: Timeout/connect-fail ≠ PASS; soft-fail prints SOFT-FAIL; hard-fail stays hard; overlay prerequisite documented

The repository MUST treat SOCKS probe Timeout and connect-fail as **not PASS**. Scheduled / soft-fail verify (when `GITHUB_EVENT_NAME` is `schedule` or `MULVAD_VERIFY_SOFT_FAIL` is truthy) MUST print a line containing `SOFT-FAIL` and MUST NOT invent green / LIVE_PASS. Dispatch (or other non-soft contexts) with `verify=true` and without soft-fail env MUST remain hard-fail (non-zero exit on probe failure). Documentation that describes verify levers MUST state the Mullvad overlay prerequisite: SOCKS hostnames resolve to RFC1918 `10.124.x` (or in-tunnel `10.64.0.1`) reachable only from a Mullvad WireGuard tunnel; public GitHub Actions runners cannot probe them. Tip floor `115837ee` (#3 CLOSED) already implements schedule soft-fail honesty in `scripts/verify_proxies.py`; this capability MUST NOT remint that product logic unless a proved falsifier appears.

#### Scenario: Soft-fail prints SOFT-FAIL and does not invent green

- **GIVEN** verify runs under schedule or `MULVAD_VERIFY_SOFT_FAIL` truthy
- **AND** HTTP or WebSocket probes do not all succeed
- **WHEN** `scripts/verify_proxies.py` finishes
- **THEN** stdout includes a `SOFT-FAIL` message naming overlay/tunnel limitation
- **AND** the process MAY exit 0 so publish can proceed
- **AND** operators MUST NOT treat that exit as probe success or LIVE_PASS

#### Scenario: Hard-fail remains hard without soft-fail env

- **GIVEN** `workflow_dispatch` with `verify=true` (or local run) without soft-fail env
- **AND** probes fail (timeout/connect-fail)
- **WHEN** `scripts/verify_proxies.py` finishes
- **THEN** the process exits non-zero (hard-fail; tip uses exit 2)
- **AND** Timeout/connect-fail is not reported as PASS

#### Scenario: Overlay prerequisite is documented where levers are described

- **GIVEN** README CI note, docs/spec.md SOCKS verify prerequisite, and (after Apply) AGENTS/skill verify docs
- **WHEN** an operator reads how to interpret CI or local verify
- **THEN** Mullvad overlay `10.124.x` / tunnel-only reachability is stated
- **AND** public GHA schedule soft-fail is not described as probe success

#### Scenario: No remint of closed #3 soft-fail without falsifier

- **GIVEN** tip ≥ `115837eed55f874ae34cd8c1bfd1a5eba74f18cf` with #3 soft-fail landed
- **WHEN** this change is applied
- **THEN** product soft-fail logic in `scripts/verify_proxies.py` / schedule path is left intact unless a proved falsifier is recorded
- **AND** propose artefacts alone do not rewrite that logic

### Requirement: Lever-first VERIFY contract

Feature: mulvad-verify-levers
Rule: Cite script and/or pytest; refuse prose-only; no invent LIVE_PASS

Brief.VERIFY and poteto/orch VERIFY claims for this repo MUST cite runnable levers: `scripts/verify_proxies.py` and/or `uv run pytest` targeting `tests/test_verify_proxies.py` (and suite). Prose-only VERIFY without a named lever MUST be refused. Agents MUST NOT invent LIVE_PASS from GHA timeouts, soft-fail exit 0, or narrative alone. Local pytest uses fixtures and does not prove public GHA overlay reachability.

#### Scenario: VERIFY cites named levers

- **GIVEN** an orch brief or agent claims VERIFY for mulvad SOCKS/proxy green
- **WHEN** the claim is accepted
- **THEN** it cites `scripts/verify_proxies.py` and/or `uv run pytest` (`tests/test_verify_proxies.py`)
- **AND** evidence path under `/workspace/orchestrate/mulvad-verify-levers/evidence/` MAY be attached when Runtime/Static Probe is recorded

#### Scenario: Prose-only VERIFY is refused

- **GIVEN** a claim that proxies are green without running a named lever
- **WHEN** a verifier evaluates the claim
- **THEN** the claim is rejected as prose-only
- **AND** no LIVE_PASS is invented from soft-fail or timeout logs

#### Scenario: Pytest fixture green ≠ GHA overlay green

- **GIVEN** `uv run pytest` passes locally using SOCKS fixtures in `tests/test_verify_proxies.py`
- **WHEN** operators interpret CI schedule soft-fail
- **THEN** local fixture PASS MUST NOT be treated as proof that public GHA reached Mullvad overlay SOCKS

### Requirement: Verification skills and poteto cite contract

Feature: mulvad-verify-levers
Rule: AGENTS (+ optional skill) describe soft vs hard + tunnel; poteto cites pstack/gbp — cite not clone

After Apply, `AGENTS.md` MUST describe soft-fail vs hard-fail verify modes and the Mullvad tunnel prerequisite for live SOCKS probes. Apply MAY add a thin `.agents/skills/verify-mulvad-proxies` skill that points at the same levers (script + pytest) without vendoring fleet skill trees. Poteto arena / interrogate / swarm handoff for long-horizon work MUST **cite** pstack and `tommy-ca/grok-build-plugins` long-horizon-swarm / WORKFLOW surfaces — cite not clone into this product repo.

#### Scenario: AGENTS documents soft vs hard after Apply

- **GIVEN** Wave-5 Apply has landed
- **WHEN** an agent reads `AGENTS.md` verify guidance
- **THEN** soft-fail (schedule / `MULVAD_VERIFY_SOFT_FAIL`) vs hard-fail (dispatch verify without soft env) is described
- **AND** tunnel / overlay prerequisite is stated
- **AND** named levers `scripts/verify_proxies.py` and pytest are present

#### Scenario: Optional thin verify skill on Apply

- **GIVEN** Apply chooses to add `.agents/skills/verify-mulvad-proxies`
- **WHEN** the skill is read
- **THEN** it is thin and points at script/pytest levers + honesty bar
- **AND** it does not vendor full intent-driven or fleet skill trees into product code paths

#### Scenario: Poteto handoff cites not clones

- **GIVEN** arena / interrogate / swarm is used for this program
- **WHEN** long-horizon swarm or pstack binding is referenced
- **THEN** cites name pstack and gbp long-horizon-swarm / tip WORKFLOW.md
- **AND** this repo does not clone those skill bodies into product trees

### Requirement: Propose-only fence and orch must-nots

Feature: mulvad-verify-levers
Rule: Apply HOLD; no remint #3; no self-hosted without Todd; dual orch forbidden; orch metadata out of product trees

Wave-4 propose MUST land OpenSpec artefacts (+ config/schema bootstrap) only. Product AGENTS/skill Apply and any optional machine-scannable soft-fail marker remain **HOLD** until Todd/Horizon go. Agents MUST NOT remint closed #3 / `mulvad-proxy-pipeline-red`. Agents MUST NOT open a self-hosted Mullvad runner without Todd ask. Dual orch is forbidden: Horizon is leaf apply orch; Drove is tick/quota only. Orchestration metadata MUST stay under `/workspace/orchestrate/mulvad-verify-levers/` (and related fleet paths), not inside unrelated product trees (`mullvad/` package, product script remints, etc.).

#### Scenario: Propose PR is OpenSpec-only

- **GIVEN** Wave-4 propose PR for `mulvad-verify-levers`
- **WHEN** the diff is reviewed
- **THEN** changes are under `openspec/` (config, schemas/intent-driven, changes/mulvad-verify-levers)
- **AND** product soft-fail logic and workflow verify steps are untouched
- **AND** Apply tasks remain HOLD

#### Scenario: Dual orch and self-hosted gates

- **GIVEN** apply or continuous-tick dispatch for this program
- **WHEN** ownership and runner scope are checked
- **THEN** Horizon owns leaf OpenSpec apply; Drove does not steal apply
- **AND** self-hosted Mullvad runner is not opened without Todd ask
- **AND** orch metadata is not committed into product package trees

### Requirement: OpenSpec intent-driven present after Apply bootstrap merge

Feature: mulvad-verify-levers
Rule: config schema intent-driven lands with propose merge; tip has openspec/

After this propose PR merges (bootstrap), tip MUST contain `openspec/config.yaml` with `schema: intent-driven` and the change under `openspec/changes/mulvad-verify-levers/`. After Wave-5 Apply archive, the NEW capability MUST exist under `openspec/specs/mulvad-verify-levers/`. Validate `--strict` MUST pass for the change before archive.

#### Scenario: Tip has intent-driven config after propose merge

- **GIVEN** the propose PR is merged to main
- **WHEN** tip is inspected
- **THEN** `openspec/config.yaml` sets `schema: intent-driven`
- **AND** project-local `openspec/schemas/intent-driven/` is present for validate
- **AND** full companion skill trees are not required in the propose PR

#### Scenario: Strict validate passes for the change

- **GIVEN** propose artefacts are complete
- **WHEN** `openspec validate mulvad-verify-levers --type change --strict` runs from the worktree
- **THEN** validation PASSes
