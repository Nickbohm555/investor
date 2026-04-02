# Phase 14: Deepen Watchlist Explanations And Follow-Up Guidance - Research

**Researched:** 2026-04-02
**Domain:** Deterministic enrichment of watchlist output in an existing strategic-report pipeline
**Confidence:** HIGH

## User Constraints

No `14-CONTEXT.md` exists, so there are no phase-specific locked decisions beyond the roadmap entry.

Repo constraints that still apply:
- Keep the current Python/FastAPI/Postgres architecture.
- Preserve the existing `ResearchOutcome -> StrategicInsightReport -> rendered email` pipeline instead of inventing a second report format for watchlist runs.
- Keep outcome branching deterministic in Python; do not move watchlist explanation quality into free-form prompt prose.
- Stay compatible with the current local-first operator workflow and the Phase 8/11 reporting contracts already persisted on run state.

Planning-relevant open decisions caused by the missing `CONTEXT.md`:
- Whether richer watchlist follow-up guidance should come from new structured fields on watchlist items or be derived from existing evidence arrays.
- Whether no-action output should be expanded at the same time or remain a lighter fallback path than watchlist runs.
- Whether the repo wants richer rendered sections only, or richer persisted report data plus rendered sections.

## Summary

Phase 14 should deepen explanation quality without undoing the deterministic report architecture established in Phase 8. The current code already supports watchlist and no-action branches, but the watchlist contract is shallow: `WatchlistOutcome.items` reuse `CandidateRecommendation`, `build_strategic_insight_report()` turns each item into `ResearchNeededItem`, and the final templates render only `uncertainty`, `follow_up_questions`, and a generic operator action. That is enough to surface caution, but not enough to explain missing evidence, unresolved contradictions, or concrete next investigation steps in a decision-grade way.

The clean path is to enrich the structured contract first, then update the prompt/pipeline and rendering to populate it. Today the LLM is asked to return `supporting_evidence`, `opposing_evidence`, `risk_notes`, and `source_summary` for every recommendation-like item. There is no explicit schema field for "missing evidence", "why this stayed on the watchlist", or "next investigation step". If Phase 14 only tweaks templates, the system will keep guessing those explanations from weak fallback data and the result will stay generic. If Phase 14 only tweaks prompts, the richer explanation will be hidden in prose and will not be durable enough for testing or future UI use.

**Primary recommendation:** treat richer watchlist guidance as a contract upgrade across three layers: expand the structured watchlist/report schemas, teach the research prompt and normalization path to populate the new fields, then render them into more useful watchlist sections with deterministic tests covering persistence and email output.

## Existing Repo Seams

### Current Watchlist Contract

- `app/schemas/research.py` defines `WatchlistOutcome(summary, items)` where `items` are plain `CandidateRecommendation` records.
- `app/services/research_prompt.py` only requires the model to populate `supporting_evidence`, `opposing_evidence`, `risk_notes`, and `source_summary`.
- `app/services/report_builder.py` maps watchlist items into `ResearchNeededItem` using `uncertainty=_build_uncertainty(...)` and `follow_up_questions=item.opposing_evidence or [outcome.summary]`.
- `app/templates/reports/strategic_report.txt.j2` and `app/templates/reports/strategic_report.html.j2` render a generic "Research Queue" section rather than a watchlist-specific explanatory surface.
- `app/graph/workflow.py` persists `finalized_outcome`, `strategic_report`, and `email_body`, so any richer watchlist guidance can already survive restart/review if it is added to structured models.

### What Is Missing

- No explicit field for missing evidence needed before promotion off the watchlist.
- No explicit field for "next investigation step" or "what to check next session".
- No explicit distinction between contradictory evidence, unknowns, and operational blockers.
- No watchlist-specific renderer section that explains why the item is not actionable now.
- No visible test source files in this workspace for report rendering/workflow behavior, so Phase 14 should plan for restoring or recreating the necessary coverage rather than assuming it already exists.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | repo existing | Expand report and research contracts safely | The repo already uses strict typed models for outcomes and reports. |
| `Jinja2` | repo existing | Render richer watchlist sections deterministically | The current report emails already render through templates. |
| `pytest` | repo existing | Lock new explanation fields and rendered output | Deterministic report behavior needs exact regression coverage. |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Existing report persistence on `RunRecord.state_payload` | repo existing | Preserve enriched watchlist guidance for approval/review history | Use when verifying richer fields survive workflow persistence. |
| Existing research loop prompt/output path | repo existing | Add new structured watchlist expectations without replacing the agent architecture | Use when extending the final JSON contract. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Schema-first watchlist enrichment | Template-only copy changes | Faster, but still derives key explanations from weak fallback fields and keeps quality shallow. |
| Deterministic follow-up guidance fields | Free-form narrative prose from the model | Richer writing style, but poor testability and weak persistence semantics. |
| Reusing the existing strategic-report pipeline | Separate watchlist-only email format | Would duplicate workflow/report logic and split the operator experience. |

## Architecture Patterns

### Pattern 1: Separate "unknowns" from "next steps"

**What:** Add dedicated structured fields for missing evidence or unresolved questions, distinct from the operator action.

**When to use:** For every watchlist item that is not promotion-ready.

**Why:** The current `follow_up_questions` list is doing too many jobs at once. The operator needs to know both what is unclear and what to do next.

### Pattern 2: Keep promotion logic deterministic and rendering explanatory

**What:** Continue deciding candidate/watchlist/no-action in Python or validated structured output, then let templates explain the watchlist state using already-classified fields.

**When to use:** Always.

**Why:** This repo has already chosen deterministic report assembly. Phase 14 should deepen explanation, not reintroduce prompt-owned branching.

### Pattern 3: Upgrade persistence and rendering together

**What:** If new watchlist explanation fields are added to the report schema, they must also be rendered and persisted in `state_payload`.

**When to use:** For any new field that matters to operator review.

**Why:** A richer email alone is not enough if approval/debug tooling cannot inspect the same data later.

### Pattern 4: Rebuild missing report tests as Wave 1 work

**What:** Assume report rendering/workflow coverage may need to be recreated in source form.

**When to use:** At the start of implementation planning.

**Why:** In this workspace snapshot, report-related source tests are not present under `tests/`, so Phase 14 should not depend on invisible coverage.

### Anti-Patterns To Avoid

- Deriving "missing evidence" entirely from `opposing_evidence`.
- Hiding next investigation steps inside `summary` prose only.
- Creating a watchlist-only template path that bypasses `StrategicInsightReport`.
- Making watchlist explanation quality dependent on rendered copy rather than persisted fields.
- Expanding watchlist output without adding verification for persistence and rendering.

## Planning Implications

Phase 14 should likely break into three plans:

1. Upgrade the watchlist/report contracts and rebuild the missing report test surface.
2. Extend the research prompt plus report builder so watchlist outcomes carry explicit missing-evidence and next-step guidance.
3. Update rendering/workflow persistence/docs so enriched watchlist explanations appear in operator output and stay durable in stored run state.

That decomposition matches the repo's existing pattern of schema first, deterministic builder second, workflow/rendering third.

## Common Pitfalls

### Pitfall 1: Treating watchlist depth as a template problem

**What goes wrong:** Output looks slightly nicer but still says little beyond generic uncertainty.

**Why it happens:** The upstream structured data never captured the missing evidence or next action explicitly.

**How to avoid:** Add new typed fields before touching the final wording.

### Pitfall 2: Collapsing all follow-up guidance into one string list

**What goes wrong:** The operator cannot tell whether an item is blocked by contradictory evidence, missing confirmation, or low conviction.

**Why it happens:** One list gets reused for uncertainty, open questions, and next steps.

**How to avoid:** Split explanatory roles into separate fields with clear semantics.

### Pitfall 3: Forgetting no-action compatibility

**What goes wrong:** Watchlist improvements accidentally break the no-action branch or create asymmetric renderer assumptions.

**Why it happens:** The report builder currently shares the `research_queue` surface for watchlist and no-action outputs.

**How to avoid:** Keep no-action valid with empty or summary-derived fallbacks, and test both branches.

### Pitfall 4: Depending on nonexistent tests

**What goes wrong:** The plan claims strong regression coverage, but the referenced source test files are not actually present.

**Why it happens:** Prior planning artifacts mention tests that are missing from the current workspace snapshot.

**How to avoid:** Make restoration or recreation of report/watchlist tests explicit in Plan 01.
