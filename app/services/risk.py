from app.schemas.workflow import Recommendation


def filter_recommendations(
    items: list[Recommendation],
    minimum_conviction: float,
    max_ideas: int,
) -> list[Recommendation]:
    seen: set[str] = set()
    accepted: list[Recommendation] = []

    for item in items:
        if item.conviction_score < minimum_conviction:
            continue
        if item.ticker in seen:
            continue
        seen.add(item.ticker)
        accepted.append(item)

    return accepted[:max_ideas]
