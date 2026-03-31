from __future__ import annotations

from typing import Callable, List, Protocol

from pydantic import TypeAdapter

from app.schemas.quiver import TickerEvidenceBundle
from app.schemas.research import ResearchOutcome
from app.services.research_prompt import build_research_prompt_payload


class InvokableLLM(Protocol):
    def invoke(self, payload: dict[str, str]) -> str:
        ...


class ResearchNode:
    def __init__(
        self,
        llm: InvokableLLM,
        prompt_builder: Callable[[str, List[TickerEvidenceBundle], dict[str, str]], dict[str, str]] = build_research_prompt_payload,
    ):
        self._agent = llm
        self._prompt_builder = prompt_builder

    def run(
        self,
        run_id: str,
        evidence_bundles: List[TickerEvidenceBundle],
        account_context: dict[str, str],
    ) -> ResearchOutcome:
        payload = self._prompt_builder(run_id, evidence_bundles, account_context)
        response = self._agent.invoke(payload)
        return TypeAdapter(ResearchOutcome).validate_json(response)
