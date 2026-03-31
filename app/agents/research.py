from __future__ import annotations

from typing import Protocol

from pydantic import TypeAdapter

from app.schemas.research import ResearchOutcome


class InvokableLLM(Protocol):
    def invoke(self, payload: dict[str, str]) -> str:
        ...


class ResearchNode:
    def __init__(self, llm: InvokableLLM):
        self._agent = llm

    def run(self, account_context: dict[str, str]) -> ResearchOutcome:
        response = self._agent.invoke(account_context)
        return TypeAdapter(ResearchOutcome).validate_json(response)
