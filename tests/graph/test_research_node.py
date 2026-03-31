from app.agents.research import ResearchNode


class FakeListLLM:
    def __init__(self, responses: list[str]):
        self._responses = responses

    def invoke(self, _: dict[str, str]) -> str:
        return self._responses.pop(0)


def test_research_node_parses_candidate_outcome():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Congress and insider signals aligned"],"broker_eligible":true}]}'
            ]
        )
    )

    result = node.run(account_context={"buying_power": "1000"})

    assert result.outcome == "candidates"
    assert result.recommendations[0].supporting_evidence == ["Congress buy"]


def test_research_node_parses_watchlist_outcome():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"outcome":"watchlist","summary":"Signals are mixed.","items":[{"ticker":"NVDA","action":"watch","conviction_score":0.64,"supporting_evidence":["Insider buy"],"opposing_evidence":["Lobbying risk"],"risk_notes":["Conflicting signals"],"source_summary":["Signals diverged"],"broker_eligible":true}]}'
            ]
        )
    )

    result = node.run(account_context={"buying_power": "1000"})

    assert result.outcome == "watchlist"
    assert result.items[0].opposing_evidence == ["Lobbying risk"]


def test_research_node_parses_no_action_outcome():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"outcome":"no_action","summary":"No qualified ideas.","reasons":["No candidates survived pruning."]}'
            ]
        )
    )

    result = node.run(account_context={"buying_power": "1000"})

    assert result.outcome == "no_action"
    assert result.reasons == ["No candidates survived pruning."]
