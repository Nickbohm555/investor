from __future__ import annotations

import argparse
import json
import httpx
import smtplib
import ssl

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import (
    ApprovalEventRecord,
    BrokerArtifactRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.db.session import get_session_factory
from app.services.research_llm import HttpResearchLLM
from app.tools.quiver import QuiverClient

_QUVER_ENDPOINTS = {
    "congresstrading": (
        "/beta/live/congresstrading",
        "get_live_congress_trading",
    ),
    "insiders": (
        "/beta/live/insiders",
        "get_live_insider_trading",
    ),
    "govcontracts": (
        "/beta/live/govcontracts",
        "get_live_government_contracts",
    ),
    "lobbying": (
        "/beta/live/lobbying",
        "get_live_lobbying",
    ),
}

_LLM_MESSAGE = "Use one Quiver tool call to inspect NVDA and stop."
_LLM_TOOL = {
    "type": "function",
    "function": {
        "name": "get_live_congress_trading",
        "description": "Inspect live congressional trading for a ticker.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
            },
            "required": ["ticker"],
        },
    },
}


def _check_smtp(settings) -> dict[str, object]:
    uses_starttls = settings.smtp_port == 587
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as client:
        if uses_starttls:
            client.starttls(context=ssl.create_default_context())
        if settings.smtp_username and settings.smtp_password:
            client.login(settings.smtp_username, settings.smtp_password)
    return {
        "host": settings.smtp_host,
        "port": settings.smtp_port,
        "uses_starttls": uses_starttls,
    }


def _check_reachability(settings) -> dict[str, object]:
    approval_probe_url = f"{settings.external_base_url.rstrip('/')}/approval/probe"
    try:
        response = httpx.get(approval_probe_url, follow_redirects=True, timeout=10)
        status_code = response.status_code
        reachable = True
    except httpx.HTTPError:
        status_code = None
        reachable = False
    return {
        "approval_probe_url": approval_probe_url,
        "status_code": status_code,
        "reachable": reachable,
    }


def _run_preflight(settings):
    quiver_client = QuiverClient(
        base_url=settings.quiver_base_url,
        api_key=settings.quiver_api_key,
    )
    quiver_checks: dict[str, dict[str, object]] = {}
    for check_name, (path, method_name) in _QUVER_ENDPOINTS.items():
        records = getattr(quiver_client, method_name)(ticker="NVDA")
        quiver_checks[check_name] = {
            "path": path,
            "status": "ok",
            "row_count": len(records),
        }

    llm = HttpResearchLLM(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    message = llm.complete_with_tools(
        messages=[{"role": "user", "content": _LLM_MESSAGE}],
        tools=[_LLM_TOOL],
        tool_choice="auto",
        parallel_tool_calls=False,
    )
    return {
        "quiver_checks": quiver_checks,
        "llm_check": {
            "path": "/chat/completions",
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "has_tool_calls": bool(message.get("tool_calls")),
        },
        "smtp_check": _check_smtp(settings),
        "external_base_url": settings.external_base_url,
        "reachability_check": _check_reachability(settings),
    }


def _trigger_scheduled(settings):
    response = httpx.post(
        settings.schedule_trigger_url,
        headers={"X-Investor-Scheduled-Trigger": settings.scheduled_trigger_token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _inspect_run(settings, run_id):
    session_factory = get_session_factory(settings.database_url)
    with session_factory() as session:
        run = session.get(RunRecord, run_id)
        if run is None:
            raise ValueError(f"Run {run_id} was not found")
        approval_event_count = session.execute(
            select(func.count()).select_from(ApprovalEventRecord).where(ApprovalEventRecord.run_id == run_id)
        ).scalar_one()
        state_transition_count = session.execute(
            select(func.count()).select_from(StateTransitionRecord).where(StateTransitionRecord.run_id == run_id)
        ).scalar_one()
        broker_artifact_count = session.execute(
            select(func.count()).select_from(BrokerArtifactRecord).where(BrokerArtifactRecord.run_id == run_id)
        ).scalar_one()
    return {
        "run_id": run.run_id,
        "status": run.status,
        "current_step": run.current_step,
        "approval_status": run.approval_status,
        "approval_event_count": approval_event_count,
        "state_transition_count": state_transition_count,
        "broker_artifact_count": broker_artifact_count,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.ops.live_proof")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("preflight")
    subparsers.add_parser("trigger-scheduled")
    inspect_run = subparsers.add_parser("inspect-run")
    inspect_run.add_argument("--run-id", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()

    if args.command == "preflight":
        payload = _run_preflight(settings)
    elif args.command == "trigger-scheduled":
        payload = _trigger_scheduled(settings)
    else:
        payload = _inspect_run(settings, args.run_id)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
