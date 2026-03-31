from __future__ import annotations

import json
import subprocess
import sys

DRY_RUN_COMMAND = "python -m app.ops.dry_run"


def test_dry_run_executes_scheduled_trigger_through_approval_and_prestage():
    result = subprocess.run(
        [sys.executable, "-m", "app.ops.dry_run"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["trigger_status"] == "started"
    assert payload["approval_status"] == "broker_prestaged"
    assert payload["artifact_count"] >= 1
    assert payload["approval_url"]
    assert payload["run_id"]
    assert payload["research_tool_call_count"] >= 2
    assert payload["research_stop_reason"] == "final_answer"
    assert payload["investigated_tickers"] == ["NVDA", "MSFT"]


def test_dry_run_prints_operator_summary_json():
    assert DRY_RUN_COMMAND == "python -m app.ops.dry_run"

    result = subprocess.run(
        [sys.executable, "-m", "app.ops.dry_run"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload) >= {
        "trigger_status",
        "approval_status",
        "run_id",
        "approval_url",
        "artifact_count",
        "log_lines",
        "research_tool_call_count",
        "research_stop_reason",
        "investigated_tickers",
    }
