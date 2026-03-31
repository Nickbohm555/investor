from __future__ import annotations

import httpx

from app.main import create_app
from app.services.research_llm import HttpResearchLLM


def test_http_research_llm_posts_openai_chat_completion_payload():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["json"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"outcome":"no_action","recommendations":[]}'
                        }
                    }
                ]
            },
        )

    llm = HttpResearchLLM(
        base_url="https://api.openai.example/v1",
        api_key="openai-test-key",
        model="gpt-4.1-mini",
        transport=httpx.MockTransport(handler),
    )

    response = llm.invoke({"system": "system prompt", "user": "user prompt"})

    assert response == '{"outcome":"no_action","recommendations":[]}'
    assert captured["url"] == "https://api.openai.example/v1/chat/completions"
    assert captured["authorization"] == "Bearer openai-test-key"
    assert '"model":"gpt-4.1-mini"' in captured["json"]
    assert '"response_format":{"type":"json_object"}' in captured["json"]


def test_create_app_uses_env_backed_research_adapter_and_no_default_quiver_transport():
    app = create_app()

    assert type(app.state.research_node._agent).__name__ == "HttpResearchLLM"
    assert app.state.quiver_transport is None
