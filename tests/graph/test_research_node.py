from app.agents.research import ResearchNode


class FakeListLLM:
    def __init__(self, responses: list[str]):
        self._responses = responses

    def invoke(self, _: dict[str, str]) -> str:
        return self._responses.pop(0)


def test_research_node_returns_structured_recommendations():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"recommendations": [{"ticker": "NVDA", "action": "buy", "conviction_score": 0.81, "rationale": "signal"}]}'
            ]
        )
    )

    result = node.run(account_context={"buying_power": "1000"})

    assert result.recommendations[0].ticker == "NVDA"
