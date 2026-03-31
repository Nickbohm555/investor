from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.research import ResearchNode
from app.config import Settings
from app.db.models import Base, BrokerArtifactRecord, RunRecord
from app.db.session import get_session_factory

DRY_RUN_COMMAND = "python -m app.ops.dry_run"
DRY_RUN_RESEARCH_RESPONSE = (
    '{"outcome":"candidates","recommendations":['
    '{"ticker":"NVDA","action":"buy","conviction_score":0.81,'
    '"supporting_evidence":["Congress buy","Insider buy"],'
    '"opposing_evidence":[],"risk_notes":["Volatile"],'
    '"source_summary":["Congress and insider signals aligned"],'
    '"broker_eligible":true}'
    ']}'
)


class MailProviderSpy:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


class StubResearchLLM:
    def __init__(self) -> None:
        self._tool_turn = 0

    def invoke(self, payload: dict[str, str]) -> str:
        return DRY_RUN_RESEARCH_RESPONSE

    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        self._tool_turn += 1
        if self._tool_turn == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "get_live_congress_trading",
                            "arguments": '{"ticker":"NVDA"}',
                        },
                    }
                ],
            }
        if self._tool_turn == 2:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {
                            "name": "get_live_insider_trading",
                            "arguments": '{"ticker":"MSFT"}',
                        },
                    }
                ],
            }
        return {
            "role": "assistant",
            "content": DRY_RUN_RESEARCH_RESPONSE,
            "tool_calls": [],
        }


class StubAlpacaClient:
    def get_account(self) -> dict:
        return {"buying_power": "1000.00", "trading_blocked": False}

    def get_asset(self, symbol: str) -> dict:
        return {"symbol": symbol, "tradable": True, "fractionable": True}


def _build_settings(database_url: str) -> Settings:
    return Settings.model_validate(
        {
            "app_name": "investor",
            "app_env": "development",
            "app_secret": "dry-run-secret",
            "database_url": database_url,
            "smtp_host": "localhost",
            "smtp_port": 1025,
            "smtp_username": "investor-user",
            "smtp_password": "smtp-password",
            "smtp_from_email": "investor@test.local",
            "daily_memo_to_email": "operator@test.local",
            "external_base_url": "https://investor.test.local",
            "schedule_cron_expression": "30 8 * * 1-5",
            "schedule_trigger_url": "http://127.0.0.1:8000/runs/trigger/scheduled",
            "scheduled_trigger_token": "dry-run-trigger-token",
            "cron_log_path": "logs/cron/daily-trigger.log",
            "quiver_base_url": "https://api.quiverquant.com",
            "quiver_api_key": "dry-run-quiver-key",
            "broker_mode": "paper",
            "alpaca_base_url": "https://paper-api.alpaca.markets",
            "alpaca_api_key": "dry-run-alpaca-key",
            "openai_api_key": "dry-run-openai-key",
            "openai_base_url": "https://api.openai.example/v1",
            "openai_model": "gpt-4.1-mini",
            "approval_token_ttl_seconds": 900,
            "research_agent_max_steps": 4,
            "research_agent_max_tool_calls": 3,
            "research_agent_max_seed_tickers": 2,
        }
    )


def _build_quiver_transport() -> httpx.MockTransport:
    payloads = {
        "/beta/live/congresstrading": [{"Ticker": "NVDA", "Transaction": "Purchase"}],
        "/beta/live/insiders": [{"Ticker": "NVDA", "Transaction": "Buy"}],
        "/beta/live/govcontracts": [{"Ticker": "NVDA", "Agency": "NASA", "Amount": "1000"}],
        "/beta/live/lobbying": [{"Ticker": "NVDA", "Client": "Example Client", "Issue": "Semiconductors"}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payloads[request.url.path])

    return httpx.MockTransport(handler)


def _apply_env_overrides(settings: Settings) -> None:
    env_values = {
        "INVESTOR_APP_NAME": settings.app_name,
        "INVESTOR_APP_ENV": settings.app_env,
        "INVESTOR_APP_SECRET": settings.app_secret,
        "INVESTOR_DATABASE_URL": settings.database_url,
        "INVESTOR_SMTP_HOST": settings.smtp_host,
        "INVESTOR_SMTP_PORT": str(settings.smtp_port),
        "INVESTOR_SMTP_USERNAME": settings.smtp_username,
        "INVESTOR_SMTP_PASSWORD": settings.smtp_password,
        "INVESTOR_SMTP_FROM_EMAIL": settings.smtp_from_email,
        "INVESTOR_DAILY_MEMO_TO_EMAIL": settings.daily_memo_to_email,
        "INVESTOR_EXTERNAL_BASE_URL": settings.external_base_url,
        "INVESTOR_SCHEDULE_CRON_EXPRESSION": settings.schedule_cron_expression,
        "INVESTOR_SCHEDULE_TRIGGER_URL": settings.schedule_trigger_url,
        "INVESTOR_SCHEDULED_TRIGGER_TOKEN": settings.scheduled_trigger_token,
        "INVESTOR_CRON_LOG_PATH": settings.cron_log_path,
        "INVESTOR_QUIVER_BASE_URL": settings.quiver_base_url,
        "INVESTOR_QUIVER_API_KEY": settings.quiver_api_key,
        "INVESTOR_BROKER_MODE": settings.broker_mode,
        "INVESTOR_ALPACA_BASE_URL": settings.alpaca_base_url,
        "INVESTOR_ALPACA_API_KEY": settings.alpaca_api_key,
        "INVESTOR_OPENAI_API_KEY": settings.openai_api_key,
        "INVESTOR_OPENAI_BASE_URL": settings.openai_base_url,
        "INVESTOR_OPENAI_MODEL": settings.openai_model,
        "INVESTOR_APPROVAL_TOKEN_TTL_SECONDS": str(settings.approval_token_ttl_seconds),
        "INVESTOR_RESEARCH_AGENT_MAX_STEPS": str(settings.research_agent_max_steps),
        "INVESTOR_RESEARCH_AGENT_MAX_TOOL_CALLS": str(settings.research_agent_max_tool_calls),
        "INVESTOR_RESEARCH_AGENT_MAX_SEED_TICKERS": str(settings.research_agent_max_seed_tickers),
    }
    for key, value in env_values.items():
        os.environ[key] = value


def main() -> int:
    log_lines: list[str] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        database_url = f"sqlite+pysqlite:///{Path(tmpdir) / 'investor.db'}"
        settings = _build_settings(database_url)
        _apply_env_overrides(settings)
        from app.main import create_app

        session_factory = get_session_factory(database_url)
        Base.metadata.create_all(bind=session_factory.kw["bind"])
        mail_provider = MailProviderSpy()
        app = create_app(
            settings=settings,
            session_factory=session_factory,
            mail_provider=mail_provider,
            research_node=ResearchNode(llm=StubResearchLLM()),
            quiver_transport=_build_quiver_transport(),
            alpaca_client_factory=lambda broker_mode: StubAlpacaClient(),
        )

        with TestClient(app) as client:
            trigger_response = client.post(
                "/runs/trigger/scheduled",
                headers={"X-Investor-Scheduled-Trigger": settings.scheduled_trigger_token},
            )
            trigger_payload = trigger_response.json()
            run_id = trigger_payload["run_id"]
            log_lines.append(f"scheduled trigger returned {trigger_payload['status']}")

            memo_text = mail_provider.sent_messages[-1]["text_body"]
            approval_url = memo_text.split("Approve: ", 1)[1].splitlines()[0].strip()
            approval_path = urlsplit(approval_url).path
            approval_response = client.get(approval_path)
            approval_payload = approval_response.json()
            log_lines.append(f"approval callback returned {approval_payload['status']}")

        with Session(session_factory.kw["bind"]) as session:
            stored_run = session.get(RunRecord, run_id)
            artifact_count = len(
                session.scalars(
                    select(BrokerArtifactRecord).where(BrokerArtifactRecord.run_id == run_id)
                ).all()
            )
        assert stored_run is not None

        print(
            json.dumps(
                {
                    "trigger_status": trigger_payload["status"],
                    "approval_status": approval_payload["status"],
                    "run_id": run_id,
                    "approval_url": approval_url,
                    "artifact_count": artifact_count,
                    "research_tool_call_count": stored_run.state_payload["research_tool_call_count"],
                    "research_stop_reason": stored_run.state_payload["research_stop_reason"],
                    "investigated_tickers": stored_run.state_payload["investigated_tickers"],
                    "log_lines": log_lines,
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
