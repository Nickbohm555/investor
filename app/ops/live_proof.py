from __future__ import annotations

import argparse
import json
import httpx

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import (
    ApprovalEventRecord,
    BrokerArtifactRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.db.session import get_session_factory
from app.ops.readiness import collect_readiness_errors
from app.services.mail_provider import inspect_smtp_connection
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
    return inspect_smtp_connection(settings)


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
    readiness_failures = collect_readiness_errors(settings)
    quiver_checks: dict[str, dict[str, object]] = {}
    llm_check: dict[str, object] = {
        "path": "/chat/completions",
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "has_tool_calls": False,
    }
    reachability_check = _check_reachability(settings)
    approval_reachability_ready = bool(reachability_check["reachable"])
    warnings = [] if approval_reachability_ready else ["approval-link-unreachable"]

    try:
        smtp_check = _check_smtp(settings)
        smtp_ready = True
        blocking_failures: list[str] = []
    except ValueError as exc:
        smtp_check = {
            "host": settings.smtp_host,
            "port": settings.smtp_port,
            "error": str(exc),
        }
        smtp_ready = False
        blocking_failures = ["smtp"]

    if readiness_failures:
        blocking_failures = readiness_failures
    else:
        quiver_client = QuiverClient(
            base_url=settings.quiver_base_url,
            api_key=settings.quiver_api_key,
        )
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
        llm_check["has_tool_calls"] = bool(message.get("tool_calls"))

    return {
        "quiver_checks": quiver_checks,
        "llm_check": llm_check,
        "smtp_check": smtp_check,
        "external_base_url": settings.external_base_url,
        "manual_trigger_url": settings.manual_trigger_url,
        "first_blocking_failure": blocking_failures[0] if blocking_failures else None,
        "reachability_check": reachability_check,
        "smtp_ready": smtp_ready,
        "approval_reachability_ready": approval_reachability_ready,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
    }


def _trigger_scheduled(settings):
    response = httpx.post(
        settings.schedule_trigger_url,
        headers={"X-Investor-Scheduled-Trigger": settings.scheduled_trigger_token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _trigger_manual(settings):
    response = httpx.post(settings.manual_trigger_url, timeout=30)
    try:
        payload = response.json()
    except ValueError:
        payload = {"body": response.text}
    return {
        "status_code": response.status_code,
        "ok": response.is_success,
        "payload": payload,
    }


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
    subparsers.add_parser("trigger-manual")
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
    elif args.command == "trigger-manual":
        payload = _trigger_manual(settings)
    elif args.command == "trigger-scheduled":
        payload = _trigger_scheduled(settings)
    else:
        payload = _inspect_run(settings, args.run_id)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
