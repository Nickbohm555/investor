from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
