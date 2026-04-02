from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_compose_stack_defines_app_managed_scheduler_runtime() -> None:
    compose_text = (PROJECT_ROOT / "docker-compose.yml").read_text()

    assert "postgres:" in compose_text
    assert "migrate:" in compose_text
    assert "app:" in compose_text
    assert "scheduler:" not in compose_text
    assert "ops/docker/start-app-runtime.sh" in compose_text


def test_scheduler_runtime_targets_existing_route() -> None:
    crontab_path = PROJECT_ROOT / "ops/scheduler/crontab"
    trigger_script_path = PROJECT_ROOT / "ops/scheduler/trigger-scheduled.sh"

    assert crontab_path.exists()
    assert trigger_script_path.exists()

    crontab_text = crontab_path.read_text()
    trigger_script_text = trigger_script_path.read_text()

    assert "CRON_TZ=America/New_York" in crontab_text
    assert "/app/ops/scheduler/trigger-scheduled.sh" in crontab_text
    assert "/runs/trigger/scheduled" in trigger_script_text
    assert "X-Investor-Scheduled-Trigger" in trigger_script_text
