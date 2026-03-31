from __future__ import annotations

import json

import httpx

AUTHORIZATION_HEADER = "Authorization: Bearer {api_key}"


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
        response = self._client.post(
            "/chat/completions",
            content=json.dumps(body, separators=(",", ":")),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
