from __future__ import annotations

import tempfile
from types import SimpleNamespace

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ApprovalEventRecord,
    Base,
    BrokerArtifactRecord,
    RecommendationRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.db.session import get_session_factory
from app.ops import live_proof


def _build_settings(database_url: str = "sqlite+pysqlite:///:memory:") -> SimpleNamespace:
    return SimpleNamespace(
        database_url=database_url,
        quiver_base_url="https://api.quiver.example",
        quiver_api_key="quiver-key",
        openai_base_url="https://llm.example/v1",
        openai_api_key="openai-key",
        openai_model="gpt-4.1-mini",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="smtp-user",
        smtp_password="smtp-pass",
        smtp_from_email="investor@example.com",
        daily_memo_to_email="operator@example.com",
        external_base_url="https://investor.example.com",
        schedule_trigger_url="http://127.0.0.1:8000/runs/trigger/scheduled",
        scheduled_trigger_token="scheduled-trigger-token",
    )


def test_preflight_reports_quiver_llm_smtp_and_external_url_checks(monkeypatch) -> None:
    settings = _build_settings()
    quiver_calls: list[tuple[str, str | None]] = []
    llm_calls: list[dict[str, object]] = []
    smtp_events: list[tuple[str, object]] = []

    class FakeQuiverClient:
        def __init__(self, *, base_url: str, api_key: str) -> None:
            assert base_url == settings.quiver_base_url
            assert api_key == settings.quiver_api_key

        def get_live_congress_trading(self, ticker: str | None = None) -> list[dict[str, str]]:
            quiver_calls.append(("congresstrading", ticker))
            return [{"Ticker": "NVDA"}]

        def get_live_insider_trading(self, ticker: str | None = None) -> list[dict[str, str]]:
            quiver_calls.append(("insiders", ticker))
            return [{"Ticker": "NVDA"}]

        def get_live_government_contracts(self, ticker: str | None = None) -> list[dict[str, str]]:
            quiver_calls.append(("govcontracts", ticker))
            return [{"Ticker": "NVDA"}]

        def get_live_lobbying(self, ticker: str | None = None) -> list[dict[str, str]]:
            quiver_calls.append(("lobbying", ticker))
            return [{"Ticker": "NVDA"}]

    class FakeResearchLLM:
        def __init__(self, *, base_url: str, api_key: str, model: str) -> None:
            assert base_url == settings.openai_base_url
            assert api_key == settings.openai_api_key
            assert model == settings.openai_model

        def complete_with_tools(
            self,
            *,
            messages: list[dict[str, object]],
            tools: list[dict[str, object]],
            tool_choice: str = "auto",
            parallel_tool_calls: bool = False,
        ) -> dict[str, object]:
            llm_calls.append(
                {
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": tool_choice,
                    "parallel_tool_calls": parallel_tool_calls,
                }
            )
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

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            smtp_events.append(("connect", (host, port, timeout)))

        def __enter__(self) -> FakeSMTP:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def starttls(self, context) -> None:
            smtp_events.append(("starttls", context))

        def login(self, username: str, password: str) -> None:
            smtp_events.append(("login", (username, password)))

    def fake_get(url: str, *, follow_redirects: bool = True, timeout: int = 10) -> httpx.Response:
        assert url == "https://investor.example.com/approval/probe"
        assert follow_redirects is True
        assert timeout == 10
        return httpx.Response(404, request=httpx.Request("GET", url))

    monkeypatch.setattr(live_proof, "QuiverClient", FakeQuiverClient)
    monkeypatch.setattr(live_proof, "HttpResearchLLM", FakeResearchLLM)
    monkeypatch.setattr(live_proof.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(live_proof.httpx, "get", fake_get)

    result = live_proof._run_preflight(settings)

    assert set(result) == {
        "quiver_checks",
        "llm_check",
        "smtp_check",
        "external_base_url",
        "reachability_check",
    }
    assert set(result["quiver_checks"]) == {
        "congresstrading",
        "insiders",
        "govcontracts",
        "lobbying",
    }
    assert quiver_calls == [
        ("congresstrading", "NVDA"),
        ("insiders", "NVDA"),
        ("govcontracts", "NVDA"),
        ("lobbying", "NVDA"),
    ]
    assert result["llm_check"]["tool_choice"] == "auto"
    assert result["llm_check"]["path"] == "/chat/completions"
    assert llm_calls[0]["messages"] == [
        {"role": "user", "content": "Use one Quiver tool call to inspect NVDA and stop."}
    ]
    assert llm_calls[0]["tools"][0]["function"]["name"] == "get_live_congress_trading"
    assert llm_calls[0]["parallel_tool_calls"] is False
    assert result["smtp_check"] == {
        "host": "smtp.example.com",
        "port": 587,
        "uses_starttls": True,
    }
    assert ("login", ("smtp-user", "smtp-pass")) in smtp_events
    assert result["external_base_url"] == "https://investor.example.com"
    assert result["reachability_check"] == {
        "approval_probe_url": "https://investor.example.com/approval/probe",
        "status_code": 404,
        "reachable": True,
    }


def test_trigger_scheduled_posts_to_configured_route_with_repo_token_header(monkeypatch) -> None:
    settings = _build_settings()
    captured: dict[str, object] = {}

    def fake_post(url: str, *, headers: dict[str, str], timeout: int = 30) -> httpx.Response:
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return httpx.Response(
            202,
            json={
                "status": "started",
                "run_id": "run-1234abcd",
                "schedule_key": "2026-04-02",
                "duplicate": False,
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(live_proof.httpx, "post", fake_post)

    result = live_proof._trigger_scheduled(settings)

    assert captured == {
        "url": "http://127.0.0.1:8000/runs/trigger/scheduled",
        "headers": {"X-Investor-Scheduled-Trigger": "scheduled-trigger-token"},
        "timeout": 30,
    }
    assert result == {
        "status": "started",
        "run_id": "run-1234abcd",
        "schedule_key": "2026-04-02",
        "duplicate": False,
    }


def test_inspect_run_reports_persisted_status_and_related_counts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        database_url = f"sqlite+pysqlite:///{tmpdir}/live-proof.db"
        session_factory = get_session_factory(database_url)
        Base.metadata.create_all(bind=session_factory.kw["bind"])
        settings = _build_settings(database_url=database_url)

        with Session(session_factory.kw["bind"]) as session:
            session.add(
                RunRecord(
                    run_id="run-1234abcd",
                    status="awaiting_review",
                    trigger_source="scheduled",
                    approval_status="pending",
                    current_step="approval",
                    schedule_key="2026-04-02",
                    replay_of_run_id=None,
                    state_payload={"finalized_outcome": {"action": "buy"}},
                )
            )
            session.add(
                RecommendationRecord(
                    run_id="run-1234abcd",
                    ticker="NVDA",
                    action="buy",
                    rationale="Signals aligned",
                )
            )
            session.add(
                ApprovalEventRecord(
                    run_id="run-1234abcd",
                    decision="approve",
                    token_id="token-1",
                )
            )
            session.add(
                StateTransitionRecord(
                    run_id="run-1234abcd",
                    from_status="triggered",
                    to_status="awaiting_review",
                    reason="Workflow advanced",
                )
            )
            session.flush()
            recommendation_id = session.execute(select(RecommendationRecord.id)).scalar_one()
            session.add(
                BrokerArtifactRecord(
                    run_id="run-1234abcd",
                    recommendation_id=recommendation_id,
                    broker_mode="paper",
                    symbol="NVDA",
                    side="buy",
                    order_type="market",
                    time_in_force="day",
                    qty="1",
                    notional=None,
                    client_order_id="run-1234abcd-1-paper",
                    status="draft_ready",
                    policy_snapshot_json={"mode": "paper"},
                )
            )
            session.commit()

        result = live_proof._inspect_run(settings, "run-1234abcd")

        assert result == {
            "run_id": "run-1234abcd",
            "status": "awaiting_review",
            "current_step": "approval",
            "approval_status": "pending",
            "approval_event_count": 1,
            "state_transition_count": 1,
            "broker_artifact_count": 1,
        }
