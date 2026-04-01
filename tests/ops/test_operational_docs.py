from __future__ import annotations

from pathlib import Path


ENV_KEYS = [
    "INVESTOR_APP_NAME",
    "INVESTOR_APP_ENV",
    "INVESTOR_APP_SECRET",
    "INVESTOR_DATABASE_URL",
    "INVESTOR_SMTP_HOST",
    "INVESTOR_SMTP_PORT",
    "INVESTOR_SMTP_USERNAME",
    "INVESTOR_SMTP_PASSWORD",
    "INVESTOR_SMTP_FROM_EMAIL",
    "INVESTOR_DAILY_MEMO_TO_EMAIL",
    "INVESTOR_EXTERNAL_BASE_URL",
    "INVESTOR_SCHEDULE_CRON_EXPRESSION",
    "INVESTOR_SCHEDULE_TIMEZONE",
    "INVESTOR_SCHEDULE_TRIGGER_URL",
    "INVESTOR_SCHEDULED_TRIGGER_TOKEN",
    "INVESTOR_CRON_LOG_PATH",
    "INVESTOR_QUIVER_BASE_URL",
    "INVESTOR_QUIVER_API_KEY",
    "INVESTOR_BROKER_MODE",
    "INVESTOR_ALPACA_BASE_URL",
    "INVESTOR_ALPACA_API_KEY",
    "INVESTOR_OPENAI_API_KEY",
    "INVESTOR_OPENAI_BASE_URL",
    "INVESTOR_OPENAI_MODEL",
    "INVESTOR_APPROVAL_TOKEN_TTL_SECONDS",
]

README_COMMANDS = [
    "pip install -e .",
    "cp .env.example .env",
    "docker compose up -d postgres",
    "alembic upgrade head",
    "python -m app.ops.dry_run",
    "uvicorn app.main:app --reload",
    "./scripts/cron-install.sh",
    "./scripts/cron-status.sh",
    "./scripts/cron-trigger.sh",
    "./scripts/cron-remove.sh",
    "python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/ops/test_dry_run.py tests/ops/test_operational_docs.py -q",
]

README_CHECKLIST_LINES = [
    "## System Architecture",
    "## Dry Run",
    "## Cron Operations",
    "## Go-Live Checklist",
    "## Acceptance Verification",
    "- SMTP credentials send to the real operator inbox",
    "- Quiver API key and base URL point to the intended account",
    "- OpenAI-compatible API key, base URL, and model are configured for ResearchNode",
    "- INVESTOR_EXTERNAL_BASE_URL resolves to the public approval host",
    "- Alpaca paper mode uses https://paper-api.alpaca.markets",
    "- INVESTOR_SCHEDULE_TIMEZONE is set to America/New_York for the managed 7:00am ET cron install",
    "- Cron is installed with ./scripts/cron-install.sh and verified with ./scripts/cron-status.sh",
]


def test_env_example_lists_all_required_operational_variables():
    env_text = Path(".env.example").read_text()

    for key in ENV_KEYS:
        assert f"{key}=" in env_text


def test_readme_documents_repo_owned_bootstrap_and_dry_run_commands():
    readme_text = Path("README.md").read_text()

    for command in README_COMMANDS:
        assert command in readme_text


def test_readme_contains_go_live_checklist_sections():
    readme_text = Path("README.md").read_text()

    for line in README_CHECKLIST_LINES:
        assert line in readme_text


def test_docs_lock_et_schedule_contract_language():
    env_text = Path(".env.example").read_text()
    readme_text = Path("README.md").read_text()

    assert "INVESTOR_SCHEDULE_TIMEZONE=America/New_York" in env_text
    assert "7:00am ET" in readme_text
    assert "INVESTOR_SCHEDULE_TIMEZONE" in readme_text


def test_readme_contains_system_architecture_section_and_truthful_boundary():
    readme_text = Path("README.md").read_text()

    assert "## System Architecture" in readme_text
    assert "docs/architecture/system-diagram.png" in readme_text
    assert "broker_prestaged" in readme_text
    assert "direct order submission" in readme_text


def test_architecture_source_and_export_assets_exist():
    assert Path("docs/architecture/system-diagram.excalidraw").is_file()
    assert Path("docs/architecture/system-diagram.png").is_file()
