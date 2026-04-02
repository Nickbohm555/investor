# Phase 14: Deepen Watchlist Explanations And Follow-Up Guidance - Research

**Researched:** 2026-04-02
**Domain:** Richer watchlist-specific report contracts and deterministic follow-up guidance over the existing strategic-report pipeline
**Confidence:** HIGH

## User Constraints

No `*-CONTEXT.md` exists for Phase 14, so there are no phase-specific locked decisions copied from upstream discussion.

Repo and roadmap constraints that still apply:
- Keep the existing Python/FastAPI/Postgres direction.
- Build on top of Phase 8 strategic reports, not the deprecated pre-report watchlist email path.
- Keep deterministic bucketing, persistence, and rendering in Python; do not move operator-facing business logic into free-form model prose.
- Preserve the existing persistence seam: richer watchlist detail should ride in `runs.state_payload["strategic_report"]` unless planning explicitly chooses SQL-queryable columns.
- Phase 14 depends on Phase 13, so planning should assume the scheduler path is the Compose-native route, not host cron.

## Summary

Phase 14 is primarily a contract problem, not a templating problem. The current report pipeline already routes watchlist output into `research_queue`, persists the report in `runs.state_payload`, and renders text/HTML through Jinja templates. The weakness is the shape of the data: `ResearchNeededItem` only carries one `uncertainty` string and one generic `follow_up_questions` list, and the builder currently derives those fields from `opposing_evidence` or the watchlist summary. That is too shallow to explain why an item is on the watchlist, what evidence is missing, and what the next investigation step should be.

The biggest planning decision is whether to keep overloading `CandidateRecommendation` for watchlist items. Do not. A candidate-ready thesis and a watchlist thesis are different states. Planning should introduce a dedicated watchlist-detail contract in `app/schemas/research.py` and a richer `ResearchNeededItem` contract in `app/schemas/reports.py`, then update the builder so watchlist guidance is assembled from explicit fields instead of heuristics over candidate evidence arrays.

No new library is needed. The established stack is already right: Pydantic for strict schema evolution, Jinja2 for deterministic rendering, FastAPI for the delivery seam, and SQLAlchemy JSON persistence for the stored report artifact. The phase should stay focused on schema depth, builder rules, renderer coverage, and restoring missing test source files for the report pipeline.

**Primary recommendation:** Add a dedicated watchlist schema with explicit uncertainty reasons, missing evidence, and next-step guidance; keep the final wording deterministic in `report_builder.py`, and store the richer result inside the existing persisted `strategic_report` payload.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | `2.12.5` | Strict watchlist and report schemas, discriminated unions, persistence-safe serialization | The repo already uses Pydantic models heavily, and current docs still support discriminated unions plus `model_dump()` for stable validated payloads. |
| `Jinja2` | `3.1.6` | Deterministic text/HTML report rendering | The current report renderer already uses Jinja with `StrictUndefined` and autoescape; Phase 14 should expand templates, not replace the renderer. |
| `FastAPI` | `0.135.3` | Existing delivery seam for trigger -> workflow -> email | No API redesign is needed; the watchlist detail flows through the same runtime seam already used by strategic reports. |
| `SQLAlchemy` | `2.0.48` | Persist richer `strategic_report` JSON inside `runs.state_payload` | The existing JSON column is enough for this phase unless planning explicitly wants queryable relational watchlist detail. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic-settings` | `2.13.1` | Optional config for follow-up limits or threshold wording | Use only if Phase 14 adds operator-tunable caps such as max follow-up steps shown per watchlist item. |
| `httpx` | `0.28.1` | Existing LLM/service transport if the research prompt contract changes | Use only if the phase expands the structured research output contract returned by the model. |
| `pytest` | `7.1.2` in local env | Builder, renderer, and workflow regression coverage | Keep pytest; do not introduce a new test framework for a schema/rendering phase. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Dedicated watchlist schema | Keep reusing `CandidateRecommendation` for watchlist items | Faster initially, but it keeps Phase 14 trapped in inference-heavy heuristics and ambiguous field meaning. |
| Existing `state_payload["strategic_report"]` JSON | New relational watchlist-detail table | Queryable, but unnecessary unless the operator needs SQL reporting over watchlist follow-ups. |
| Python-owned explanation assembly | Free-form model-authored watchlist prose | Sounds richer, but loses determinism and makes report tests fragile. |

**Installation:**
```bash
pip install -e .
```

**Version verification:** Verified from PyPI JSON on 2026-04-02.
- `pydantic` `2.12.5` — published 2025-11-26
- `Jinja2` `3.1.6` — published 2025-03-05
- `FastAPI` `0.135.3` — published 2026-04-01
- `SQLAlchemy` `2.0.48` — published 2026-03-02
- `pydantic-settings` `2.13.1` — published 2026-02-19
- `httpx` `0.28.1` — published 2024-12-06

## Architecture Patterns

### Recommended Project Structure

```text
app/
├── schemas/
│   ├── research.py          # add dedicated watchlist item schema
│   └── reports.py           # expand ResearchNeededItem fields
├── services/
│   ├── report_builder.py    # map structured watchlist data into report items
│   ├── report_render.py     # unchanged renderer seam
│   └── research_prompt.py   # expand prompt contract only if model output must grow
├── templates/reports/
│   ├── strategic_report.txt.j2
│   └── strategic_report.html.j2
└── graph/workflow.py        # no seam change beyond passing richer report data
tests/
├── services/
│   ├── test_report_builder.py
│   └── test_report_render.py
└── graph/
    └── test_workflow_reporting.py
```

### Pattern 1: Give Watchlist Output Its Own Schema
**What:** Replace the current `WatchlistOutcome.items: list[CandidateRecommendation]` shape with a watchlist-specific model that carries explicit uncertainty and follow-up fields.

**When to use:** Always for this phase.

**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
from pydantic import BaseModel, Field
from typing import Literal


class WatchlistRecommendation(BaseModel):
    ticker: str
    thesis: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)
    contradictory_evidence: list[str] = Field(default_factory=list)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class WatchlistOutcome(BaseModel):
    outcome: Literal["watchlist"]
    summary: str
    items: list[WatchlistRecommendation]
```

### Pattern 2: Keep Explanation Assembly In The Builder
**What:** `report_builder.py` should convert raw watchlist detail into operator-facing report fields. Templates should only present those fields.

**When to use:** Always; this keeps tests deterministic and wording reviewable.

**Example:**
```python
def _build_research_needed_item(item: WatchlistRecommendation, fallback: str) -> ResearchNeededItem:
    return ResearchNeededItem(
        ticker=item.ticker.upper(),
        thesis=item.thesis or fallback,
        uncertainty_reasons=item.uncertainty_reasons or [fallback],
        missing_evidence=item.missing_evidence,
        next_steps=item.next_steps or ["Re-check on the next run."],
        operator_action="Collect the missing evidence before approval.",
    )
```

### Pattern 3: Use Hybrid Provenance For Follow-Up Guidance
**What:** Let the model emit raw structured gaps and suggested next steps, but keep ordering, fallbacks, and operator wording in Python.

**When to use:** If Phase 14 expands the research prompt/output contract.

**Example:**
```python
# Source: repo pattern in app/services/research_prompt.py + app/services/report_builder.py
{
    "system": (
        "Return JSON only. For watchlist items include uncertainty_reasons, "
        "missing_evidence, and next_steps arrays."
    )
}
```

### Pattern 4: Persist Richer Detail In Existing Report JSON
**What:** Expand `StrategicInsightReport` and write the result back through the existing `state_payload["strategic_report"]` path.

**When to use:** Default for this phase.

**Example:**
```python
# Source: repo seam in app/graph/workflow.py
state["strategic_report"] = report.model_dump(mode="python")
```

### Anti-Patterns to Avoid
- **Reusing `CandidateRecommendation` forever:** A watchlist item is not a weak candidate; it is a different operator state with different required fields.
- **Treating `opposing_evidence` as `follow_up_questions`:** That is the core weakness in the current builder and should be removed.
- **Template-owned logic:** Do not add large `if` trees in Jinja to infer why a ticker is on the watchlist.
- **Relational persistence by default:** Do not add a new table unless planning proves the operator needs SQL queries over watchlist explanations.
- **Prompt-only enrichment:** Richer prose without richer schema will regress determinism immediately.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Watchlist explanation state | Ad-hoc dicts passed into templates | Pydantic models in `app/schemas/research.py` and `app/schemas/reports.py` | Validation prevents half-populated explanation fields and impossible states. |
| HTML/text rendering | Manual string concatenation in `app/services/email.py` | Existing Jinja2 renderer with expanded templates | The renderer seam already exists and is easier to snapshot-test. |
| Missing-evidence inference | Heuristics over `opposing_evidence` alone | Explicit `missing_evidence` and `next_steps` arrays in the schema | Contradictory evidence is not the same thing as a next investigation action. |
| Persistence redesign | New watchlist persistence subsystem | Existing `runs.state_payload` JSON | The phase is about richer report content, not a new reporting datastore. |
| Free-form follow-up prose | Custom markdown parsing or string post-processing | Structured arrays plus deterministic builder phrasing | Safer, easier to test, and easier to evolve. |

**Key insight:** The planner should treat Phase 14 as a typed-data expansion of the Phase 8 report system. The most expensive mistake would be trying to make the watchlist feel richer through prose-only rendering changes.

## Common Pitfalls

### Pitfall 1: Watchlist Detail Is Still Inferred From Candidate Fields
**What goes wrong:** The report sounds repetitive or vague because the builder can only recycle `opposing_evidence` and `summary`.
**Why it happens:** `WatchlistOutcome` currently reuses `CandidateRecommendation`.
**How to avoid:** Add watchlist-specific fields for uncertainty, missing evidence, and next steps.
**Warning signs:** Multiple watchlist items render nearly identical follow-up text despite different evidence states.

### Pitfall 2: The Renderer Starts Owning Business Logic
**What goes wrong:** HTML and text templates drift apart and become hard to test.
**Why it happens:** Richer watchlist output tempts the implementation to move conditionals into Jinja.
**How to avoid:** Keep derivation in `report_builder.py`; templates should mostly loop and print.
**Warning signs:** The text and HTML templates contain different fallback logic or different field-selection rules.

### Pitfall 3: Model Output Becomes Richer But Validation Stays Shallow
**What goes wrong:** The LLM starts returning richer fields, but the schema ignores or loosely accepts them, so regressions slip through.
**Why it happens:** Prompt changes land without updating the Pydantic contract.
**How to avoid:** Change `app/schemas/research.py` first, then update prompts and tests against the new contract.
**Warning signs:** Report fields are sometimes empty even though the model trace shows detailed follow-up guidance.

### Pitfall 4: Planning Assumes Report Tests Already Exist
**What goes wrong:** The phase claims strong verification, but the repo snapshot only contains `__pycache__` artifacts under `tests/`.
**Why it happens:** Prior planning docs reference test files that are absent from source control in this workspace.
**How to avoid:** Make report test restoration or recreation a Wave 0 task.
**Warning signs:** `python3 -m pytest -q` reports `no tests ran`.

### Pitfall 5: Richer Watchlist Guidance Leaks Into Approval Semantics
**What goes wrong:** The implementation starts changing approval/rejection or broker-prestage behavior while touching report data.
**Why it happens:** The workflow and report seams meet in `app/graph/workflow.py`.
**How to avoid:** Keep this phase scoped to report content and persisted state shape; do not alter approval route behavior.
**Warning signs:** Planner tasks mention approval-token, broker, or route-state-machine changes without a direct watchlist requirement.

## Code Examples

Verified patterns from official sources and current repo seams:

### Discriminated Union For Explicit Watchlist Branches
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
ResearchOutcome = Annotated[
    CandidateOutcome | WatchlistOutcome | NoActionOutcome,
    Field(discriminator="outcome"),
]
```

### Serialize A Validated Report For Persistence And Rendering
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
payload = report.model_dump(mode="python")
```

### Strict Jinja Environment For Dual Text/HTML Templates
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
Environment(
    loader=FileSystemLoader("app/templates/reports"),
    autoescape=select_autoescape(["html", "xml"]),
    undefined=StrictUndefined,
)
```

### Recommended Watchlist Report Shape
```python
# Source: repo adaptation over app/schemas/reports.py
class ResearchNeededItem(BaseModel):
    bucket: Literal["research"] = "research"
    ticker: str
    thesis: str = ""
    uncertainty_reasons: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    operator_action: str = ""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Branch-aware memo bodies for `recommendations/watchlist/no_action` | Typed strategic report with `immediate`, `defer`, and `research` buckets | Phase 8 on 2026-03-31 | Phase 14 should extend `research_queue`, not resurrect the older memo shape. |
| Watchlist summary plus inferred follow-up text | Explicit watchlist-detail schema with structured gaps and next steps | Recommended for Phase 14 | Makes watchlist guidance testable and less repetitive. |
| Manual string assembly in email code | Jinja2 text/HTML rendering | Phase 8 on 2026-03-31 | Richer watchlist guidance should expand templates, not replace the renderer. |

**Deprecated/outdated:**
- Reusing pre-Phase-8 `DailyMemoContent` as the main planning seam for watchlist work. The workflow now sends strategic reports, not the old watchlist memo contract.
- Deriving research follow-ups from `opposing_evidence` alone. That is a stopgap, not a scalable watchlist explanation model.

## Open Questions

1. **Should richer watchlist detail be derived entirely in Python or emitted by the model?**
   - What we know: The current builder only has `summary`, `opposing_evidence`, and generic candidate fields to work with.
   - What's unclear: Whether those fields are enough to generate useful missing-evidence and next-step guidance without expanding the research schema.
   - Recommendation: Plan a hybrid approach. Add explicit model-returned arrays for raw watchlist gaps and next steps, then keep final wording and fallback ordering in Python.

2. **Does Phase 14 need relational persistence for watchlist guidance?**
   - What we know: `runs.state_payload` already persists `strategic_report`, and that is enough for review and baseline comparison.
   - What's unclear: Whether the operator wants SQL queries or dashboard filtering over watchlist follow-ups before any v2 UI work.
   - Recommendation: Default to JSON-only persistence. Add DB work only if planning discovers a concrete query need.

3. **Should the current `ResearchNeededItem` be expanded in place or replaced by a more specific model?**
   - What we know: Existing templates and builder already expect `research_queue: list[ResearchNeededItem]`.
   - What's unclear: Whether a backwards-compatible field expansion is cleaner than a rename.
   - Recommendation: Expand `ResearchNeededItem` in place unless planning finds multiple distinct research item types.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest 7.1.2` |
| Config file | none — see Wave 0 |
| Quick run command | `python3 -m pytest tests/services/test_report_builder.py tests/services/test_report_render.py tests/graph/test_workflow_reporting.py -q` |
| Full suite command | `python3 -m pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| `TBD-14-01` | Watchlist items explain uncertainty, missing evidence, and next investigation steps from structured fields | unit | `python3 -m pytest tests/services/test_report_builder.py -q` | ❌ Wave 0 |
| `TBD-14-02` | Text and HTML reports render richer watchlist guidance consistently | unit | `python3 -m pytest tests/services/test_report_render.py -q` | ❌ Wave 0 |
| `TBD-14-03` | Workflow persists and emails the richer strategic report without changing approval flow | integration | `python3 -m pytest tests/graph/test_workflow_reporting.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/services/test_report_builder.py tests/services/test_report_render.py -q`
- **Per wave merge:** `python3 -m pytest tests/services/test_report_builder.py tests/services/test_report_render.py tests/graph/test_workflow_reporting.py -q`
- **Phase gate:** `python3 -m pytest -q`

### Wave 0 Gaps

- [ ] `tests/services/test_report_builder.py` — source file missing in this workspace snapshot; recreate or restore before claiming builder coverage.
- [ ] `tests/services/test_report_render.py` — source file missing in this workspace snapshot; recreate or restore before renderer work.
- [ ] `tests/graph/test_workflow_reporting.py` — source file missing in this workspace snapshot; recreate or restore before workflow-level regression claims.
- [ ] `pytest.ini` or equivalent config — optional but useful if planning wants stable test discovery rules instead of implicit defaults.
- [ ] Baseline verification artifact — `python3 -m pytest -q` currently exits with code 5 and reports `no tests ran`; treat that as an environment gap, not a passing suite.

## Sources

### Primary (HIGH confidence)
- Repo inspection: `app/services/report_builder.py`, `app/schemas/reports.py`, `app/graph/workflow.py`, `app/services/report_render.py`, `app/services/research_prompt.py`, `app/schemas/research.py`
- https://docs.pydantic.dev/latest/concepts/unions/ - discriminated union patterns for explicit output branches
- https://docs.pydantic.dev/latest/concepts/models/ - `model_dump()` and validated model serialization
- https://jinja.palletsprojects.com/en/stable/api/ - `Environment`, `StrictUndefined`, and `select_autoescape`
- https://pypi.org/pypi/pydantic/json - latest package version and publish date
- https://pypi.org/pypi/Jinja2/json - latest package version and publish date
- https://pypi.org/pypi/fastapi/json - latest package version and publish date
- https://pypi.org/pypi/sqlalchemy/json - latest package version and publish date

### Secondary (MEDIUM confidence)
- https://pypi.org/pypi/pydantic-settings/json - supporting package version and publish date
- https://pypi.org/pypi/httpx/json - supporting package version and publish date

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependency decision is needed, and versions were verified from current PyPI metadata.
- Architecture: HIGH - repo seams are clear and Phase 8 already established the correct report pipeline.
- Pitfalls: MEDIUM - most pitfalls are strongly supported by current code inspection, but final watchlist-field shape still needs planning confirmation.

**Research date:** 2026-04-02
**Valid until:** 2026-05-02
