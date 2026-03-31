from __future__ import annotations

from typing import Protocol

from app.schemas.workflow import ResearchResult


class InvokableLLM(Protocol):
    def invoke(self, payload: dict[str, str]) -> str:
        ...


class ResearchNode:
    def __init__(self, llm: InvokableLLM):
        self._agent = llm

    def run(self, account_context: dict[str, str]) -> ResearchResult:
        response = self._agent.invoke(account_context)
        return ResearchResult.model_validate_json(response)
