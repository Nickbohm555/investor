from __future__ import annotations

import json
from urllib.parse import urlsplit

import httpx

AUTHORIZATION_HEADER = "Authorization: Bearer {api_key}"


def provider_capability_missing(base_url: str) -> str | None:
    path = urlsplit(base_url).path.rstrip("/")
    if path.endswith("/v1"):
        return None
    return "INVESTOR_OPENAI_BASE_URL does not expose the required /v1 OpenAI-compatible tool-calling surface"


class HttpResearchLLM:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": AUTHORIZATION_HEADER.format(api_key=api_key).split(": ", 1)[1]},
            transport=transport,
        )

    def invoke(self, payload: dict[str, str]) -> str:
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": payload["system"]},
                {"role": "user", "content": payload["user"]},
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._post_chat_completion(body)
        return response["choices"][0]["message"]["content"]

    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        body = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls,
        }
        response = self._post_chat_completion(body)
        return response["choices"][0]["message"]

    def _post_chat_completion(self, body: dict[str, object]) -> dict[str, object]:
        response = self._client.post(
            "/chat/completions",
            content=json.dumps(body, separators=(",", ":")),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
