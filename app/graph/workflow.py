from app.graph import nodes


class CompiledInvestorWorkflow:
    def __init__(self, research_node):
        self._research_node = research_node

    def invoke(self, state: dict) -> dict:
        loaded = nodes.load_context(state)
        research_result = nodes.research(loaded, self._research_node)
        recommendations = nodes.risk_filter(research_result)
        email = nodes.compose_email(loaded["run_id"], recommendations)
        nodes.send_email(email)
        return nodes.await_human_review(
            {**loaded, "recommendations": recommendations},
            email,
        )

    def resume(self, state: dict, decision: str) -> dict:
        if decision != "approve":
            return {**state, "status": "rejected"}
        handed_off = nodes.handoff_to_alpaca(state)
        return nodes.finalize(handed_off)


def compile_workflow(research_node) -> CompiledInvestorWorkflow:
    return CompiledInvestorWorkflow(research_node=research_node)
