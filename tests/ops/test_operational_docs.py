from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_15_DIR = PROJECT_ROOT / ".planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end"
PHASE_15_RUNBOOK = PHASE_15_DIR / "15-LIVE-PROOF-RUNBOOK.md"
PHASE_15_RESULT = PHASE_15_DIR / "15-LIVE-PROOF-RESULT.md"


def test_readme_requires_docker_native_scheduler_commands() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "docker compose up -d --build" in readme_text
    assert "docker compose logs -f migrate app" in readme_text
    assert "docker compose down -v" in readme_text


def test_readme_removes_host_cron_workflow_language() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "./scripts/cron-install.sh" not in readme_text
    assert "./scripts/cron-status.sh" not in readme_text
    assert "./scripts/cron-trigger.sh" not in readme_text
    assert "./scripts/cron-remove.sh" not in readme_text
    assert "logs/cron/daily-trigger.log" not in readme_text
    assert "scheduler service" not in readme_text
    assert "app container owns the scheduler process" in readme_text


def test_readme_mentions_shared_research_queue_guidance_sections() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "Watchlist and no-action items now explain why the idea is not actionable, what evidence is missing, which questions remain unresolved, and what to check on the next session." in readme_text


def test_readme_links_phase_15_live_proof_runbook() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "See `.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-LIVE-PROOF-RUNBOOK.md` for the real-credential live proof workflow." in readme_text
    assert "python -m app.ops.live_proof preflight" in readme_text
    assert "python -m app.ops.live_proof trigger-scheduled" in readme_text
    assert "python -m app.ops.live_proof inspect-run --run-id" in readme_text


def test_phase_15_runbook_covers_reachability_preflight_and_persisted_state_checks() -> None:
    runbook_text = PHASE_15_RUNBOOK.read_text()

    assert "## Reachability" in runbook_text
    assert "## Preflight" in runbook_text
    assert "## Start The Runtime" in runbook_text
    assert "## Trigger The Live Run" in runbook_text
    assert "## Inbox Verification" in runbook_text
    assert "## Approval Callback" in runbook_text
    assert "## Persisted State Verification" in runbook_text
    assert "## Observed Logs" in runbook_text
    assert "## Failure Markers" in runbook_text
    assert "python -m app.ops.live_proof preflight" in runbook_text
    assert "python -m app.ops.live_proof trigger-scheduled" in runbook_text
    assert "python -m app.ops.live_proof inspect-run --run-id" in runbook_text
    assert "docker compose up -d --build" in runbook_text
    assert "docker compose logs -f migrate app" in runbook_text


def test_phase_15_result_template_requires_operator_visible_proof_fields() -> None:
    result_text = PHASE_15_RESULT.read_text()

    assert "run_id:" in result_text
    assert "scheduled_trigger_status:" in result_text
    assert "approval_probe_url:" in result_text
    assert "approval_probe_status_code:" in result_text
    assert "memo_delivered_to:" in result_text
    assert "approval_link_host:" in result_text
    assert "approval_callback_status:" in result_text
    assert "current_step:" in result_text
    assert "approval_status:" in result_text
    assert "scheduled_trigger_log_line:" in result_text
    assert "memo_delivery_log_line:" in result_text
    assert "final_run_status:" in result_text
    assert "approval_event_count:" in result_text
    assert "state_transition_count:" in result_text
    assert "broker_artifact_count:" in result_text
    assert "remaining_manual_steps:" in result_text
