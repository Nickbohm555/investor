from __future__ import annotations

from types import SimpleNamespace

import httpx

from app.ops import live_proof


def _build_settings() -> SimpleNamespace:
    return SimpleNamespace(
        quiver_base_url="https://api.quiver.example",
        quiver_api_key="quiver-key",
        openai_base_url="https://llm.example/v1",
        openai_api_key="openai-key",
        openai_model="gpt-4.1-mini",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_security="auto",
        smtp_username="smtp-user",
        smtp_password="smtp-pass",
        smtp_from_email="investor@example.com",
        daily_memo_to_email="operator@example.com",
        external_base_url="https://investor.example.com",
        manual_trigger_url="http://127.0.0.1:8000/runs/trigger",
        schedule_trigger_url="http://127.0.0.1:8000/runs/trigger/scheduled",
        scheduled_trigger_token="scheduled-trigger-token",
    )


def test_parser_includes_trigger_manual_subcommand() -> None:
    parser = live_proof._build_parser()

    args = parser.parse_args(["trigger-manual"])

    assert args.command == "trigger-manual"


def test_trigger_manual_posts_to_configured_manual_route_and_preserves_response_payload(monkeypatch) -> None:
    settings = _build_settings()
    captured: dict[str, object] = {}

    def fake_post(url: str, *, timeout: int = 30) -> httpx.Response:
        captured["url"] = url
        captured["timeout"] = timeout
        return httpx.Response(
            202,
            json={"status": "started", "run_id": "run-1234abcd"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(live_proof.httpx, "post", fake_post)

    result = live_proof._trigger_manual(settings)

    assert captured == {
        "url": "http://127.0.0.1:8000/runs/trigger",
        "timeout": 30,
    }
    assert result["status_code"] == 202
    assert result["ok"] is True
    assert result["payload"]["run_id"] == "run-1234abcd"


def test_preflight_returns_exact_first_readiness_failure_and_skips_quiver_and_llm(monkeypatch) -> None:
    settings = _build_settings()
    quiver_used = False
    llm_used = False

    class ForbiddenQuiverClient:
        def __init__(self, **kwargs) -> None:
            nonlocal quiver_used
            quiver_used = True

    class ForbiddenResearchLLM:
        def __init__(self, **kwargs) -> None:
            nonlocal llm_used
            llm_used = True

    monkeypatch.setattr(
        live_proof,
        "collect_readiness_errors",
        lambda _settings: ["INVESTOR_QUIVER_BASE_URL must not equal https://example.test"],
    )
    monkeypatch.setattr(live_proof, "QuiverClient", ForbiddenQuiverClient)
    monkeypatch.setattr(live_proof, "HttpResearchLLM", ForbiddenResearchLLM)
    monkeypatch.setattr(
        live_proof,
        "_check_smtp",
        lambda _settings: {"host": settings.smtp_host, "port": settings.smtp_port},
    )
    monkeypatch.setattr(
        live_proof,
        "_check_reachability",
        lambda _settings: {
            "approval_probe_url": "https://investor.example.com/approval/probe",
            "status_code": None,
            "reachable": False,
        },
    )

    result = live_proof._run_preflight(settings)

    assert result["blocking_failures"] == ["INVESTOR_QUIVER_BASE_URL must not equal https://example.test"]
    assert result["first_blocking_failure"] == "INVESTOR_QUIVER_BASE_URL must not equal https://example.test"
    assert result["warnings"] == ["approval-link-unreachable"]
    assert quiver_used is False
    assert llm_used is False
