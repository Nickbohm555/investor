from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_15_DIR = PROJECT_ROOT / ".planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end"
PHASE_15_RUNBOOK = PHASE_15_DIR / "15-LIVE-PROOF-RUNBOOK.md"
PHASE_15_RESULT = PHASE_15_DIR / "15-LIVE-PROOF-RESULT.md"
PHASE_19_DIR = PROJECT_ROOT / ".planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency"
PHASE_19_RUNBOOK = PHASE_19_DIR / "19-LIVE-PROOF-RUNBOOK.md"
PHASE_19_RESULT = PHASE_19_DIR / "19-LIVE-PROOF-RESULT.md"
QUIVER_RESEARCH_FLOW_CONTRACT = PROJECT_ROOT / "docs/architecture/quiver-research-flow-contract.md"
QUIVER_RESEARCH_FLOW_EXCALIDRAW = PROJECT_ROOT / "docs/architecture/quiver-research-flow.excalidraw"
QUIVER_RESEARCH_FLOW_PNG = PROJECT_ROOT / "docs/architecture/quiver-research-flow.png"


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


def test_readme_links_phase_19_live_proof_runbook() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "See `.planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RUNBOOK.md` for the current SMTP delivery proof workflow." in readme_text
    assert "python -m app.ops.live_proof preflight" in readme_text
    assert "python -m app.ops.live_proof trigger-scheduled" in readme_text
    assert "python -m app.ops.live_proof inspect-run --run-id <run_id>" in readme_text


def test_phase_19_runbook_treats_approval_reachability_as_non_blocking() -> None:
    runbook_text = PHASE_19_RUNBOOK.read_text()

    assert "## Preflight" in runbook_text
    assert "## Start The Runtime" in runbook_text
    assert "## Trigger The Live Run" in runbook_text
    assert "## Inbox Verification" in runbook_text
    assert "## Approval Host Verification" in runbook_text
    assert "## Persisted State Verification" in runbook_text
    assert "## Observed Logs" in runbook_text
    assert "## Failure Markers" in runbook_text
    assert "approval reachability is a warning for Phase 19, not a blocker" in runbook_text


def test_phase_19_result_template_records_smtp_proof_without_callback_execution() -> None:
    result_text = PHASE_19_RESULT.read_text()

    assert "run_id:" in result_text
    assert "scheduled_trigger_status:" in result_text
    assert "memo_delivered_to:" in result_text
    assert "approval_link_host:" in result_text
    assert "approval_callback_status: skipped-for-phase-19" in result_text
    assert "smtp_ready:" in result_text
    assert "approval_reachability_ready:" in result_text
    assert "blocking_failures:" in result_text
    assert "warnings:" in result_text
    assert "scheduled_trigger_log_line:" in result_text
    assert "memo_delivery_log_line:" in result_text
    assert "current_step:" in result_text
    assert "approval_status:" in result_text
    assert "final_run_status:" in result_text
    assert "remaining_manual_steps:" in result_text


def test_readme_links_quiver_research_flow_asset() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "## Quiver Research Flow" in readme_text
    assert "docs/architecture/quiver-research-flow.png" in readme_text


def test_quiver_research_flow_assets_exist() -> None:
    assert QUIVER_RESEARCH_FLOW_EXCALIDRAW.exists()
    assert QUIVER_RESEARCH_FLOW_PNG.exists()


def test_quiver_research_flow_docs_name_the_exact_four_live_endpoints() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text()
    contract_text = QUIVER_RESEARCH_FLOW_CONTRACT.read_text()
    excalidraw_text = QUIVER_RESEARCH_FLOW_EXCALIDRAW.read_text()

    for content in (readme_text, contract_text, excalidraw_text):
        assert "/beta/live/congresstrading" in content
        assert "/beta/live/insiders" in content
        assert "/beta/live/govcontracts" in content
        assert "/beta/live/lobbying" in content
        assert "broad unusual legislative trade signal" in content
        assert "ticker-specific corporate insider confirmation" in content
        assert "contract-backed demand / revenue context" in content
        assert "policy/regulatory interest context" in content
