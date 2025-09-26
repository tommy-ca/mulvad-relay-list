from pathlib import Path

import yaml


def load_workflow() -> dict:
    workflow = Path(".github/workflows/proxy-pipeline.yml")
    assert workflow.exists(), "proxy-pipeline workflow must exist"
    data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    if "on" not in data and True in data:
        data["on"] = data.pop(True)
    return data


def test_proxy_pipeline_workflow_has_schedule_and_pipeline_step() -> None:
    data = load_workflow()
    triggers = data.get("on", {})
    assert "schedule" in triggers, "workflow should define a schedule trigger"
    cron_entries = triggers["schedule"]
    assert any(
        entry.get("cron") == "0 * * * *" for entry in cron_entries
    ), "workflow must trigger at the top of every hour"

    job = data["jobs"]["proxy-pipeline"]
    steps = job["steps"]
    resolve_step = next(step for step in steps if step.get("id") == "resolve")
    assert "Resolve pipeline arguments" in resolve_step.get("name", "")
    run_step = next(step for step in steps if step.get("name") == "Run relay pipeline")
    assert "${{ steps.resolve.outputs.args }}" in run_step.get("run", "")

    assert job.get("concurrency", {}).get("group") == "mullvad-relay-pipeline"
    assert job.get("concurrency", {}).get("cancel-in-progress") is False


def test_workflow_exposes_manual_inputs_with_defaults() -> None:
    data = load_workflow()
    dispatch = data.get("on", {}).get("workflow_dispatch")
    assert dispatch is not None, "workflow should support manual dispatch"
    inputs = dispatch.get("inputs", {})

    assert "countries" in inputs
    assert "providers_allow" in inputs
    assert "limit" in inputs
    verify_input = inputs.get("verify", {})
    assert verify_input.get("default") is False
    assert verify_input.get("type") == "boolean"
    emit_input = inputs.get("emit_canonical", {})
    assert emit_input.get("default") is False
    assert emit_input.get("type") == "boolean"


def test_workflow_runs_verification_when_requested() -> None:
    data = load_workflow()
    steps = data["jobs"]["proxy-pipeline"]["steps"]
    verification_step = next(step for step in steps if step.get("name") == "Run verification probes")
    assert verification_step.get("if") == "steps.resolve.outputs.verify == 'true'"
    assert "scripts/verify_proxies.py" in verification_step.get("run", "")


def test_publish_job_guards_credentials() -> None:
    data = load_workflow()
    steps = data["jobs"]["publish-artifacts"]["steps"]
    guard_step = next(step for step in steps if step.get("name") == "Guard publication credentials")
    assert "GITHUB_TOKEN" in guard_step.get("run", "")
