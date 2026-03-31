from __future__ import annotations

import pytest
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


def test_http_research_llm_complete_with_tools_posts_serial_tool_payload(
    llm_tool_capability_fixture,
):
    llm = HttpResearchLLM(
        base_url="https://api.openai.example/v1",
        api_key="openai-test-key",
        model="gpt-4.1-mini",
        transport=llm_tool_capability_fixture["transport"],
    )

    response = llm.complete_with_tools(
        messages=[{"role": "user", "content": "Investigate NVDA"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "lookup_quiver_ticker",
                    "parameters": {"type": "object"},
                },
            }
        ],
    )

    captured = llm_tool_capability_fixture["captured"]
    assert captured["url"] == "https://api.openai.example/v1/chat/completions"
    assert captured["authorization"] == "Bearer openai-test-key"
    assert '"tools":[{"type":"function","function":{"name":"lookup_quiver_ticker","parameters":{"type":"object"}}}]' in captured["json"]
    assert '"tool_choice":"auto"' in captured["json"]
    assert '"parallel_tool_calls":false' in captured["json"]
    assert response["tool_calls"][0]["function"]["name"] == "lookup_quiver_ticker"


def test_http_research_llm_invoke_remains_valid_for_final_json_only_turns(
    llm_structured_final_response_fixture,
):
    llm = HttpResearchLLM(
        base_url="https://api.openai.example/v1",
        api_key="openai-test-key",
        model="gpt-4.1-mini",
        transport=llm_structured_final_response_fixture,
    )

    response = llm.invoke({"system": "system prompt", "user": "user prompt"})

    assert response == '{"outcome":"no_action","summary":"Hold","reasons":["Weak evidence"]}'


def test_http_research_llm_complete_with_tools_surfaces_provider_capability_failure(
    llm_unsupported_provider_transport,
):
    llm = HttpResearchLLM(
        base_url="https://api.openai.example/v1",
        api_key="openai-test-key",
        model="gpt-4.1-mini",
        transport=llm_unsupported_provider_transport,
    )

    with pytest.raises(httpx.HTTPStatusError):
        llm.complete_with_tools(
            messages=[{"role": "user", "content": "Investigate NVDA"}],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "lookup_quiver_ticker",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        )
