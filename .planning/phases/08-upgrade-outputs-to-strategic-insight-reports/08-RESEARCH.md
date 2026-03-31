# Phase 8: Upgrade Outputs To Strategic Insight Reports - Research

**Researched:** 2026-03-31
**Domain:** Deterministic strategic report generation over loop-based research output
**Confidence:** MEDIUM

## Summary

Phase 8 should not let the model write the final operator email directly. The stable architecture is a two-step pipeline: Phase 7 produces typed research output plus traceable evidence, then Phase 8 converts that into a typed `StrategicInsightReport` with explicit action buckets, change summaries, and uncertainty flags. Final text and HTML rendering should stay in deterministic Python so the operator sees "what changed, why it matters, and what to do next" without making the delivered report hard to snapshot-test.

The current codebase is close to the right seam but not the right shape. `CompiledInvestorWorkflow._build_memo_content()` currently collapses outcomes into `DailyMemoContent`, and `compose_recommendation_email()` still concatenates plain text/HTML strings. That is too flat for strategic reporting. Plan this phase around a richer report schema, a comparison layer that diffs the current run against the previous delivered run, and a renderer that emits text and HTML from templates rather than inline string assembly.

The main planning risk is treating "strategic insight" as prompt wording. It is a data-contract problem first. If action buckets, thesis deltas, research gaps, and uncertainty reasons are not explicit fields, the model will hide them in prose and deterministic review will degrade immediately. Keep scoring, bucketing, ordering, and fallback phrasing in Python. Use the LLM only for structured synthesis where it adds value.

**Primary recommendation:** Add a typed `StrategicInsightReport` model, compute change-aware action buckets in Python against the previous delivered run, and render the final email/report through Jinja2 templates from validated structured data.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | `2.12.5` | Report schemas, discriminated section models, serialization for persistence/tests | Official docs support discriminated unions and `model_dump()`/JSON schema generation, which fits a report contract that must stay strict and testable |
| `Jinja2` | `3.1.6` | Deterministic text and HTML report rendering | Standard Python templating engine with inheritance, inclusion, and autoescape support; better fit than manual string assembly once sections multiply |
| `httpx` | `0.28.1` | Existing OpenAI-compatible transport for any structured synthesis call | Already in repo and adequate for current sync adapter pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic-settings` | `2.13.1` | Report config: max items, comparison window, wording thresholds | Use for operator-tunable limits without hard-coding report policy |
| `pytest` | `7.1.2` in the current local env | Snapshot-like renderer tests and deterministic workflow assertions | Use the existing test framework; no framework change is needed for this phase |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typed report model plus templates | Free-form LLM-authored memo body | Faster to prototype, but fails the determinism requirement and makes review diffs noisy |
| Jinja2 templates | Continue manual string concatenation in `app/services/email.py` | Fine for the current three-section memo, but brittle once report sections and reuse increase |
| Python-owned action bucketing | Let the model decide final `immediate/defer/research` labels in prose | Harder to test and easier to drift when prompts change |

**Installation:**
```bash
pip install "Jinja2==3.1.6"
```

**Version verification:**
- `pydantic` `2.12.5` — PyPI latest, published 2025-11-26
- `Jinja2` `3.1.6` — PyPI latest, published 2025-03-05
- `httpx` `0.28.1` — PyPI latest, published 2024-12-06
- `pydantic-settings` `2.13.1` — PyPI latest, published 2026-02-19

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── schemas/
│   ├── research.py             # Phase 7 research outcome
│   └── reports.py              # Strategic report contract and section models
├── services/
│   ├── report_compare.py       # Previous-run comparison and delta classification
│   ├── report_builder.py       # Build StrategicInsightReport from research + history
│   ├── report_render.py        # Jinja2 text/html rendering
│   └── email.py                # Thin transport wrapper over rendered output
├── templates/
│   └── reports/
│       ├── strategic_report.txt.j2
│       ├── strategic_report.html.j2
│       └── partials/
└── graph/
    └── workflow.py             # Compose/build/send report after research completes
tests/
├── services/
│   ├── test_report_compare.py
│   ├── test_report_builder.py
│   └── test_report_render.py
└── graph/
    └── test_workflow_reporting.py
```

### Pattern 1: Treat the report as a first-class schema
**What:** Add explicit report models instead of overloading `DailyMemoContent`.
**When to use:** For all Phase 8 output boundaries: builder, renderer, persistence, tests.
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ImmediateActionItem(BaseModel):
    bucket: Literal["immediate"]
    ticker: str
    thesis: str
    change_summary: str
    why_now: str
    operator_action: str


class DeferredItem(BaseModel):
    bucket: Literal["defer"]
    ticker: str
    thesis: str
    change_summary: str
    defer_reason: str
    next_check: str


class ResearchNeededItem(BaseModel):
    bucket: Literal["research"]
    ticker: str
    thesis: str
    uncertainty: str
    follow_up_questions: list[str]


ReportItem = Annotated[
    ImmediateActionItem | DeferredItem | ResearchNeededItem,
    Field(discriminator="bucket"),
]


class StrategicInsightReport(BaseModel):
    run_id: str
    baseline_run_id: str | None = None
    headline: str
    summary: str
    items: list[ReportItem]
    dropped_tickers: list[str] = Field(default_factory=list)
```

### Pattern 2: Build report data before rendering
**What:** Compare the current run against the previous delivered run and classify changes before any template rendering.
**When to use:** Always; "what changed" must come from structured comparison, not prose-only prompting.
**Example:**
```python
def classify_change(*, current, previous_by_ticker) -> str:
    previous = previous_by_ticker.get(current.ticker)
    if previous is None:
        return "new thesis"
    if current.conviction_score > previous.conviction_score:
        return "conviction increased"
    if current.conviction_score < previous.conviction_score:
        return "conviction decreased"
    if current.risk_notes != previous.risk_notes:
        return "risk profile changed"
    return "signal mix unchanged"
```

### Pattern 3: Keep model output structured and narrow
**What:** If the LLM is used for report synthesis, require a strict JSON-shaped intermediate object and validate it before report building.
**When to use:** Only for summary/headline/thesis synthesis where deterministic Python text would be too weak.
**Example:**
```python
# Source: https://developers.openai.com/api/docs/guides/structured-outputs
class InsightDraft(BaseModel):
    headline: str
    thesis: str
    why_now: str
    uncertainty: str | None = None
    follow_up_questions: list[str] = Field(default_factory=list)


draft = InsightDraft.model_validate_json(llm_response)
```

### Pattern 4: Render from templates, not inline concatenation
**What:** Use one Jinja environment to render `.txt` and `.html` versions from the same report object.
**When to use:** For all final operator-facing output.
**Example:**
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

env = Environment(
    loader=FileSystemLoader("app/templates/reports"),
    autoescape=select_autoescape(["html", "xml"]),
    undefined=StrictUndefined,
)

text_body = env.get_template("strategic_report.txt.j2").render(report=report.model_dump())
html_body = env.get_template("strategic_report.html.j2").render(report=report.model_dump())
```

### Anti-Patterns to Avoid
- **Prompt-only reporting:** Do not ask the model to emit final email prose directly.
- **String diffing rendered memos:** Compute deltas from structured recommendation/report objects, not from prior email bodies.
- **Overloading `DailyMemoContent`:** A flat `recommendations/watchlist/no_action` shape cannot cleanly express immediate, defer, and research-needed branches with change reasons.
- **Renderer-owned business logic:** Templates should present already-classified items, not decide action buckets or comparison outcomes.
- **Using current-run data only:** Phase 8 explicitly needs "what changed," which requires a baseline run or explicit "no prior baseline" handling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Final report prose generation | Free-form prompt that returns a blob of email text | Typed report model plus deterministic renderer | Preserves testability, reviewability, and stable operator wording |
| HTML escaping | Manual `html.escape()` sprinkled through long string builders | Jinja2 autoescape for HTML templates | Safer and easier once sections/partials expand |
| Report branching | Nested `if` trees over `DailyMemoContent` | Discriminated Pydantic section models | Keeps impossible report states out of the renderer |
| Change detection | Regex or line-by-line diff on past emails | Compare current vs previous structured outcomes by ticker and status | Email wording will change; underlying recommendations should remain comparable |
| Missing-field tolerance | Silent dict access and best-effort rendering | `StrictUndefined` and Pydantic validation | Fail fast when Phase 7 stops supplying a required report field |

**Key insight:** "Strategic insight" is mostly a contract and comparison problem. The more of it that lives in deterministic data structures, the easier it is to keep the operator output trustworthy.

## Common Pitfalls

### Pitfall 1: No stable baseline for "what changed"
**What goes wrong:** The report claims changes, but comparisons are inconsistent or impossible after reruns.
**Why it happens:** The phase reuses only the current run state and never chooses a canonical prior delivered run.
**How to avoid:** Define one baseline rule up front, preferably the most recent completed run whose report was actually sent.
**Warning signs:** Different reruns compare against different historical states for the same day.

### Pitfall 2: Action buckets drift with prompt edits
**What goes wrong:** An item moves from "immediate" to "research" because wording changed, not because evidence changed.
**Why it happens:** Final bucketing is left to the model.
**How to avoid:** Compute bucket selection in Python from validated fields such as conviction, risk, and uncertainty markers.
**Warning signs:** Snapshot tests fail with semantic relabeling but identical evidence.

### Pitfall 3: Renderer quietly drops missing data
**What goes wrong:** Reports send with blank sections, missing follow-ups, or malformed headings.
**Why it happens:** Manual string composition and permissive template rendering ignore absent fields.
**How to avoid:** Use `StrictUndefined` in Jinja and Pydantic models with explicit required fields.
**Warning signs:** Empty HTML paragraphs or missing bullet bodies appear without test failures.

### Pitfall 4: Historical comparison is performed on rendered text
**What goes wrong:** Minor wording changes create noisy diffs and false "change" signals.
**Why it happens:** The implementation compares memo bodies instead of structured objects.
**How to avoid:** Persist and compare structured report inputs or structured finalized outcomes by ticker.
**Warning signs:** A template edit causes every ticker to appear as changed.

### Pitfall 5: Phase 8 depends on Phase 7 traces that were never persisted
**What goes wrong:** The planner assumes access to reasoning steps, but only the final ranked list is available.
**Why it happens:** Phase 7 may stop at producing a final recommendation object.
**How to avoid:** Make Phase 8 planning explicitly require the Phase 7 output contract to include evidence summaries, thesis text, and uncertainty markers, or add a small persistence extension first.
**Warning signs:** Report builder has to reconstruct why a ticker mattered from the email body or raw tool logs.

## Code Examples

Verified patterns from official sources:

### Discriminated report sections
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
ReportItem = Annotated[
    ImmediateActionItem | DeferredItem | ResearchNeededItem,
    Field(discriminator="bucket"),
]
```

### Serialize validated models for rendering
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
payload = report.model_dump()
```

### Jinja environment with recommended autoescaping
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
env = Environment(
    loader=FileSystemLoader("app/templates/reports"),
    autoescape=select_autoescape(["html", "xml"]),
    undefined=StrictUndefined,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prompt returns final prose or loosely structured JSON | Prompt returns strict structured objects that are validated before rendering | OpenAI structured outputs guide current as of 2026-03-31 | Makes LLM synthesis usable without giving up deterministic delivery contracts |
| Inline string assembly for emails | Template-driven text/HTML rendering with shared data model | Long-standing standard pattern in Jinja 3.x docs | Keeps presentation separate from business rules and lowers formatting churn |
| Ranked list only | Change-aware report with action buckets, thesis deltas, and research gaps | This phase | Aligns the operator surface with actual decision support rather than raw ranking |

**Deprecated/outdated:**
- Building richer operator reports by extending `compose_recommendation_email()` with more string concatenation. That path will become brittle immediately once partials and repeated sections appear.

## Open Questions

1. **What exact baseline should the report compare against?**
   - What we know: Phase 8 needs "what changed" and the current system persists run records and recommendation records.
   - What's unclear: Whether the baseline is the most recent completed run, the most recent delivered report, or the most recent primary scheduled run.
   - Recommendation: Lock this in planning before task breakdown; "most recent delivered report" is the safest operator-facing rule.

2. **Does Phase 7 persist enough structured reasoning for Phase 8?**
   - What we know: Phase 7 is intended to add loop-based tool use and research traces.
   - What's unclear: Whether those traces will be persisted in a builder-friendly shape or only logged.
   - Recommendation: Add an explicit Phase 7/8 seam document or a first task that inventories the final Phase 7 output contract.

3. **Should the strategic report be email-only or also stored as a first-class artifact?**
   - What we know: Current dry-run and workflow tests center on delivered email content.
   - What's unclear: Whether future audit/history features will need the final structured report persisted separately.
   - Recommendation: Build the structured report object first and render email from it; persistence can then be added with minimal redesign if needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 7.1.2` |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/services/test_report_compare.py tests/services/test_report_builder.py tests/services/test_report_render.py tests/graph/test_workflow_reporting.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-08-01 | Reports explain signal changes, thesis updates, or uncertainty instead of only ranked tickers | unit | `python -m pytest tests/services/test_report_builder.py -q` | ❌ Wave 0 |
| SC-08-02 | Delivered report distinguishes immediate actions, defer cases, and research-needed items | unit | `python -m pytest tests/services/test_report_render.py -q` | ❌ Wave 0 |
| SC-08-03 | Email/report output remains deterministic enough for local review | unit/integration | `python -m pytest tests/graph/test_workflow_reporting.py tests/ops/test_dry_run.py -q` | ❌ / ✅ existing dry-run |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/services/test_report_compare.py tests/services/test_report_builder.py tests/services/test_report_render.py -q`
- **Per wave merge:** `python -m pytest tests/graph/test_workflow_reporting.py tests/services/test_email.py tests/graph/test_workflow.py -q`
- **Phase gate:** `python -m pytest -q`

### Wave 0 Gaps
- [ ] `tests/services/test_report_compare.py` — proves previous-run diff logic and stable change labels
- [ ] `tests/services/test_report_builder.py` — proves bucket classification and uncertainty/research-gap handling
- [ ] `tests/services/test_report_render.py` — proves deterministic text/HTML output and template-required fields
- [ ] `tests/graph/test_workflow_reporting.py` — proves workflow uses the new builder/renderer seam instead of the old flat memo path

## Sources

### Primary (HIGH confidence)
- Pydantic unions docs — discriminated unions and `Field(discriminator=...)`: https://docs.pydantic.dev/latest/concepts/unions/
- Pydantic models docs — `model_dump()` and serialization behavior: https://docs.pydantic.dev/latest/concepts/models/
- Jinja API docs — `Environment`, `select_autoescape`, and recommended autoescaping setup: https://jinja.palletsprojects.com/en/stable/api/
- Jinja template docs — template inheritance and block structure: https://jinja.palletsprojects.com/en/stable/templates/
- OpenAI structured outputs guide — strict schema-shaped model outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- PyPI `pydantic` page — latest version `2.12.5`, released 2025-11-26: https://pypi.org/project/pydantic/
- PyPI `Jinja2` page — latest version `3.1.6`, released 2025-03-05: https://pypi.org/project/Jinja2/
- PyPI `httpx` page — latest version `0.28.1`, released 2024-12-06: https://pypi.org/project/httpx/
- PyPI `pydantic-settings` page — latest version `2.13.1`, released 2026-02-19: https://pypi.org/project/pydantic-settings/

### Secondary (MEDIUM confidence)
- Repository code inspection of `app/graph/workflow.py`, `app/services/email.py`, `app/schemas/workflow.py`, and existing workflow/email tests to identify the current memo/report seam

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - official docs strongly support Pydantic and Jinja2, but the exact need for a direct `Jinja2` dependency depends on how much Phase 8 expands rendering beyond the current inline builder
- Architecture: MEDIUM - grounded in current repo seams and official docs, but depends on the exact persisted output contract that Phase 7 lands
- Pitfalls: MEDIUM - strongly supported by the current code shape and by standard typed-renderer patterns, but not all historical-report persistence details are implemented yet

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
