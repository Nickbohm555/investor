from tests.graph.test_workflow import MailProviderSpy, StubQuiverClient, StubResearchNode, make_engine, make_settings

from app.graph.workflow import compile_workflow


def test_workflow_invoke_builds_report_and_persists_strategic_report_payload():
    engine = make_engine(research_node=StubResearchNode(), mail_provider=MailProviderSpy())

    paused = engine.start_run(run_id="run-123", quiver_client=StubQuiverClient())

    assert paused["state_payload"]["strategic_report"]["headline"] == "1 immediate | 0 defer | 0 research"
    assert paused["state_payload"]["strategic_report"]["summary"] == "Compared against no prior delivered run; dropped tickers: none."
    assert "Strategic Insight Report" in paused["state_payload"]["email_body"]


def test_workflow_invoke_marks_dropped_tickers_from_baseline_run():
    workflow = compile_workflow(
        research_node=StubResearchNode(),
        settings=make_settings(),
        mail_provider=MailProviderSpy(),
        evidence_builder=lambda **_: [],
    )

    paused = workflow.invoke(
        {
            "run_id": "run-123",
            "quiver_client": StubQuiverClient(),
            "baseline_report": {
                "run_id": "run-prev",
                "strategic_report": {"run_id": "run-prev"},
                "finalized_outcome": {
                    "outcome": "candidates",
                    "recommendations": [
                        {
                            "ticker": "AMD",
                            "action": "buy",
                            "conviction_score": 0.7,
                            "supporting_evidence": ["Insider buy"],
                            "opposing_evidence": [],
                            "risk_notes": ["Execution"],
                            "source_summary": ["AI demand"],
                            "broker_eligible": True,
                        }
                    ],
                },
            },
        }
    )

    assert paused["baseline_run_id"] == "run-prev"
    assert paused["strategic_report"]["dropped_tickers"] == ["AMD"]
