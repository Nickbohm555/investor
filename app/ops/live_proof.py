from __future__ import annotations

import httpx
import smtplib

from app.services.research_llm import HttpResearchLLM
from app.tools.quiver import QuiverClient


def _run_preflight(settings):
    return {}


def _trigger_scheduled(settings):
    return {}


def _inspect_run(settings, run_id):
    return {}


def main(argv: list[str] | None = None) -> int:
    return 0
