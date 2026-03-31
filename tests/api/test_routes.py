import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.agents.research import ResearchNode
from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.tokens import sign_approval_token


class MailProviderSpy:
    def __init__(self) -> None:
        self.sent_messages = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


class StubAlpacaClient:
    def get_account(self) -> dict:
        return {"buying_power": "1000.00", "trading_blocked": False}

    def get_asset(self, symbol: str) -> dict:
        assert symbol == "NVDA"
        return {"symbol": "NVDA", "tradable": True, "fractionable": True}


class StubResearchLLM:
    def invoke(self, payload: dict[str, str]) -> str:
        return (
            '{"outcome":"candidates","recommendations":['
            '{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy","Insider buy"],'
            '"opposing_evidence":[],"risk_notes":["Volatile"],'
            '"source_summary":["Congress and insider signals aligned"],"broker_eligible":true}'
            ']}'
        )

    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        if not any(message.get("role") == "tool" for message in messages):
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
        return {
            "role": "assistant",
            "content": self.invoke({"system": "", "user": ""}),
            "tool_calls": [],
        }


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


def _build_app(tmp_path, monkeypatch):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
    monkeypatch.setenv("INVESTOR_DATABASE_URL", database_url)
    app = create_app(
        mail_provider=MailProviderSpy(),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(),
        research_node=ResearchNode(llm=StubResearchLLM()),
        quiver_transport=_build_quiver_transport(),
    )
    return app


def test_app_starts_with_test_settings():
    app = create_app(
        research_node=ResearchNode(llm=StubResearchLLM()),
        quiver_transport=_build_quiver_transport(),
    )
    app.state.mail_provider = MailProviderSpy()

    assert app is not None


def test_health_route_returns_ok():
    app = create_app(
        research_node=ResearchNode(llm=StubResearchLLM()),
        quiver_transport=_build_quiver_transport(),
    )
    app.state.mail_provider = MailProviderSpy()
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_route_returns_ok_after_readiness_passes(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_manual_trigger_starts_a_run(tmp_path, monkeypatch):
    client = TestClient(_build_app(tmp_path, monkeypatch))

    response = client.post("/runs/trigger")

    assert response.status_code == 202
    assert response.json()["status"] == "started"


def test_manual_trigger_persists_public_approval_links(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/runs/trigger")

    assert response.status_code == 202
    run_id = response.json()["run_id"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, run_id)

    assert stored is not None
    approval_prefix = f"{app.state.settings.external_base_url}/approval/"
    assert approval_prefix in stored.state_payload["email_body"]
    assert stored.state_payload["research_trace"][0]["tool_name"] == "get_live_congress_trading"
    assert stored.state_payload["research_tool_call_count"] == 1
    assert stored.state_payload["investigated_tickers"] == ["NVDA"]


def test_trigger_persists_strategic_report_and_baseline_run_id(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    with Session(app.state.session_factory.kw["bind"]) as session:
        session.add(
            RunRecord(
                run_id="run-prev",
                status="completed",
                trigger_source="manual",
                approval_status="approve",
                current_step="completed",
                created_at=datetime.utcnow() - timedelta(days=1),
                updated_at=datetime.utcnow() - timedelta(days=1),
                state_payload={
                    "strategic_report": {"run_id": "run-prev"},
                    "email_body": "Strategic Insight Report",
                    "finalized_outcome": {
                        "outcome": "candidates",
                        "recommendations": [
                            {
                                "ticker": "AMD",
                                "action": "buy",
                                "conviction_score": 0.7,
                                "supporting_evidence": ["Insider buy"],
                                "opposing_evidence": [],
                                "risk_notes": ["Execution"],
                                "source_summary": ["AI demand"],
                                "broker_eligible": True,
                            }
                        ],
                    },
                },
            )
        )
        session.commit()

    response = client.post("/runs/trigger")

    assert response.status_code == 202
    run_id = response.json()["run_id"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, run_id)

    assert stored is not None
    assert "strategic_report" in stored.state_payload
    assert "baseline_run_id" in stored.state_payload
    assert "email_body" in stored.state_payload


def test_trigger_ignores_undelivered_runs_when_selecting_baseline(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    with Session(app.state.session_factory.kw["bind"]) as session:
        session.add_all(
            [
                RunRecord(
                    run_id="run-prev",
                    status="completed",
                    trigger_source="manual",
                    approval_status="approve",
                    current_step="completed",
                    created_at=datetime.utcnow() - timedelta(days=2),
                    updated_at=datetime.utcnow() - timedelta(days=2),
                    state_payload={
                        "strategic_report": {"run_id": "run-prev"},
                        "email_body": "Strategic Insight Report",
                        "finalized_outcome": {
                            "outcome": "candidates",
                            "recommendations": [
                                {
                                    "ticker": "AMD",
                                    "action": "buy",
                                    "conviction_score": 0.7,
                                    "supporting_evidence": ["Insider buy"],
                                    "opposing_evidence": [],
                                    "risk_notes": ["Execution"],
                                    "source_summary": ["AI demand"],
                                    "broker_eligible": True,
                                }
                            ],
                        },
                    },
                ),
                RunRecord(
                    run_id="run-newer-undelivered",
                    status="awaiting_human_review",
                    trigger_source="manual",
                    approval_status="pending",
                    current_step="awaiting_review",
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    updated_at=datetime.utcnow() - timedelta(hours=1),
                    state_payload={
                        "strategic_report": {"run_id": "run-newer-undelivered"},
                        "email_body": "Strategic Insight Report",
                        "finalized_outcome": {
                            "outcome": "candidates",
                            "recommendations": [],
                        },
                    },
                ),
            ]
        )
        session.commit()

    response = client.post("/runs/trigger")

    assert response.status_code == 202
    run_id = response.json()["run_id"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, run_id)

    assert stored is not None
    assert stored.state_payload["baseline_run_id"] == "run-prev"


def test_approval_callback_resumes_a_paused_run(persisted_run):
    app = persisted_run["app"]
    client = persisted_run["client"]
    run_id = persisted_run["run_id"]
    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=900,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 200
    assert response.json() == {"status": "broker_prestaged", "run_id": run_id}


def test_trigger_persists_run_and_approval_reuses_same_thread(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    trigger_response = client.post("/runs/trigger")

    assert trigger_response.status_code == 202
    run_id = trigger_response.json()["run_id"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, run_id)
        recommendations = session.query(RecommendationRecord).filter_by(run_id=run_id).all()

    assert stored is not None
    assert stored.status == "awaiting_review"
    assert stored.current_step == "awaiting_review"
    assert recommendations
    assert not hasattr(app.state, "workflow_store")
    assert isinstance(stored.state_payload["evidence_bundles"], list)
    assert stored.state_payload["research_trace"][0]["tool_name"] == "get_live_congress_trading"
    assert stored.state_payload["research_stop_reason"] == "final_answer"
    assert stored.state_payload["finalized_outcome"]["outcome"] == "candidates"

    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )
    approval_response = client.get(f"/approval/{token}")

    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "broker_prestaged"

    with Session(app.state.session_factory.kw["bind"]) as session:
        updated = session.get(RunRecord, run_id)
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()

    assert updated is not None
    assert updated.status == "broker_prestaged"
    assert len(approval_events) == 1
    assert approval_events[0].decision == "approve"
    approval_prefix = f"{app.state.settings.external_base_url}/approval/"
    assert approval_prefix in stored.state_payload["email_body"]


def test_archived_pre_phase6_run_returns_410(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    with Session(app.state.session_factory.kw["bind"]) as session:
        archived_run = RunRecord(
            run_id="archived-run",
            status="archived_pre_phase6",
            trigger_source="manual",
            approval_status="archived",
            current_step="archived_pre_phase6",
            state_payload={"archived_reason": "phase6_cutover"},
        )
        session.add(archived_run)
        session.commit()

    token = sign_approval_token(
        run_id="archived-run",
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 410
    assert response.json() == {
        "detail": "Run was archived during the Phase 6 cutover and can no longer be approved"
    }


def test_invalid_approval_token_returns_400(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/approval/not-a-real-token")

    assert response.status_code == 400
    assert response.json() == {"detail": "Approval token invalid"}


def test_expired_approval_token_returns_410(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    client.post("/runs/trigger")
    app.state.settings.approval_token_ttl_seconds = -1
    token = sign_approval_token(
        run_id="run-expired",
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 410
    assert response.json() == {"detail": "Approval token expired"}


def test_unknown_run_approval_returns_404(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    token = sign_approval_token(
        run_id="missing-run",
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}


def test_duplicate_approval_returns_409_and_keeps_single_event(persisted_run):
    app = persisted_run["app"]
    client = persisted_run["client"]
    run_id = persisted_run["run_id"]
    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    first = client.get(f"/approval/{token}")
    second = client.get(f"/approval/{token}")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json() == {"detail": "Approval already recorded"}

    with Session(app.state.session_factory.kw["bind"]) as session:
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()

    assert len(approval_events) == 1


def test_stale_approval_returns_409(persisted_run):
    app = persisted_run["app"]
    client = persisted_run["client"]
    run_id = persisted_run["run_id"]
    reject_token = sign_approval_token(
        run_id=run_id,
        decision="reject",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    rejected = client.get(f"/approval/{reject_token}")
    stale = client.get(f"/approval/{approve_token}")

    assert rejected.status_code == 200
    assert stale.status_code == 410
    assert stale.json() == {"detail": "Approval already processed"}
