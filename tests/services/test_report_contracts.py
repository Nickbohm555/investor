from __future__ import annotations

import app.schemas.research as research_schema
from app.schemas.reports import ResearchNeededItem


def test_watchlist_outcome_items_expose_explicit_guidance_fields() -> None:
    watchlist_candidate = getattr(research_schema, "WatchlistCandidate", None)

    assert watchlist_candidate is not None
    assert watchlist_candidate.__bases__[0] is research_schema.CandidateRecommendation
    assert watchlist_candidate.model_fields["watchlist_reason"].default == ""
    assert watchlist_candidate.model_fields["missing_evidence"].default_factory() == []
    assert watchlist_candidate.model_fields["unresolved_questions"].default_factory() == []
    assert watchlist_candidate.model_fields["next_steps"].default_factory() == []
    assert research_schema.WatchlistOutcome.model_fields["items"].annotation == list[watchlist_candidate]


def test_research_needed_item_exposes_named_watchlist_guidance_fields() -> None:
    field_names = set(ResearchNeededItem.model_fields)

    assert field_names == {
        "bucket",
        "ticker",
        "thesis",
        "watchlist_reason",
        "missing_evidence",
        "unresolved_questions",
        "next_steps",
        "operator_action",
    }
    assert "uncertainty" not in field_names
    assert "follow_up_questions" not in field_names
