def build_alpaca_handoff(run_id: str, recommendations: list) -> dict:
    return {
        "run_id": run_id,
        "recommendations": [item.model_dump() for item in recommendations],
    }
