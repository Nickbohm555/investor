# Phase 2: Quiver Research And Ranking - Research

**Researched:** 2026-03-31
**Domain:** Quiver multi-signal ingestion, evidence-rich recommendation schemas, and deterministic ranking
**Confidence:** HIGH

## Summary

Phase 2 should stay inside the existing Python/FastAPI/Pydantic/httpx stack and expand the current thin Quiver client into a typed multi-endpoint adapter. The minimum dataset set that directly satisfies `RSCH-01` is Quiver live congressional trading, live insider trading, live government contracts, and live lobbying. Quiver's current API docs expose all four as first-party endpoints, and the response contracts are structured enough to normalize before any LLM call.

The planner should treat the LLM as a synthesis step, not the ranking engine. Deterministic pruning, duplicate collapse, broker-eligibility filtering, and final sort order should happen in Python after structured validation. The prompt contract should only transform a normalized evidence bundle into a typed outcome: ranked candidates, watchlist, or no-action. That is the cleanest way to satisfy `RSCH-02`, `RSCH-03`, and `RSCH-04` without letting prompt drift or model variance change delivery behavior.

The main implementation risk is schema sloppiness. Quiver returns mixed naming conventions and several monetary/date fields as strings, while the current repo only validates a single flat recommendation shape. Use dedicated Quiver models, a normalized per-ticker evidence model, and a discriminated top-level recommendation outcome. That keeps the workflow testable and prevents forced picks when evidence is weak or contradictory.

**Primary recommendation:** Extend the existing `httpx` Quiver adapter to fetch four typed datasets, normalize them into per-ticker evidence bundles, ask the LLM for a discriminated structured recommendation outcome, then apply deterministic ranking and watchlist/no-action gating in Python.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RSCH-01 | System queries a broad Quiver signal set including congressional trading, insider activity, government contracts, and lobbying before ranking ideas | Use Quiver live endpoints for congress trading, insiders, gov contracts, and lobbying with typed models and a normalization layer before synthesis |
| RSCH-02 | Each recommendation includes supporting evidence, contradictory evidence, risk notes, and a concise source summary | Use a structured Pydantic recommendation schema with explicit evidence lists, risk notes, and source summaries validated before ranking |
| RSCH-03 | System produces ranked candidates with deterministic pruning by conviction, duplication, and broker eligibility | Keep ranking and pruning in Python with stable score calculation, duplicate collapse by ticker, eligibility filtering, and deterministic tie-breakers |
| RSCH-04 | System can send a no-action or watchlist memo when evidence is weak or conflicting | Use a discriminated outcome model with `candidates`, `watchlist`, and `no_action` variants plus explicit thresholds for weak/conflicting evidence |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `httpx` | `0.28.1` | Quiver API transport | Already in repo; supports sync testable clients with `MockTransport` and keeps external IO at the edge |
| `pydantic` | `2.12.5` | Typed Quiver payloads, normalized evidence models, structured recommendation outputs | Best fit for strict validation, JSON parsing, and discriminated union outcomes |
| `fastapi` | `0.135.2` | Expose typed trigger and run APIs | Already in repo and supports `response_model` validation for any new Phase 2 response surfaces |
| `pytest` | `9.0.2` | Unit and adapter tests | Already present; sufficient for deterministic ranking, schema, and client coverage |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic-settings` | `2.13.1` | Quiver config and future ranking thresholds | Keep dataset toggles, thresholds, and API settings in env-backed config |
| `sqlalchemy` | `2.0.48` | Persist normalized research outputs in later phases | Use only if Phase 2 needs new persisted result detail beyond current in-memory flow |
| `alembic` | `1.18.4` | Schema migrations for any new research/result columns | Use when Phase 2 expands persisted recommendation detail |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom `httpx` Quiver adapter | `quiverquant` PyPI package `0.2.2` | The package exists, but its latest PyPI release is from 2023-06-09 and is pandas-oriented; a repo-local adapter matches the current architecture and Quiver's current OpenAPI better |
| Deterministic Python ranking | LLM-only ranking | Faster to prototype, but fails `RSCH-03` because ordering, pruning, and watchlist gating become nondeterministic |
| Discriminated outcome models | Flat recommendation list with sentinel flags | Harder to validate and easier to mishandle no-action/watchlist paths |

**Installation:**
```bash
pip install \
  "fastapi==0.135.2" \
  "httpx==0.28.1" \
  "pydantic==2.12.5" \
  "pydantic-settings==2.13.1" \
  "pytest==9.0.2"
```

**Version verification:**
- `fastapi` `0.135.2` — PyPI latest, published 2026-03-23
- `httpx` `0.28.1` — PyPI latest, published 2024-12-06
- `pydantic` `2.12.5` — PyPI latest, published 2025-11-26
- `pydantic-settings` `2.13.1` — PyPI latest, published 2026-02-19
- `sqlalchemy` `2.0.48` — PyPI latest, published 2026-03-02
- `alembic` `1.18.4` — PyPI latest, published 2026-02-10
- `pytest` `9.0.2` — PyPI latest, published 2025-12-06

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── agents/
│   └── research.py              # LLM synthesis over normalized evidence
├── schemas/
│   ├── quiver.py                # Raw Quiver endpoint models
│   ├── research.py              # Normalized evidence and structured output models
│   └── workflow.py              # Thin workflow-facing envelopes if needed
├── services/
│   ├── research_prompt.py       # Prompt assembly from normalized evidence
│   ├── ranking.py               # Deterministic score, prune, dedupe, tie-break
│   └── quiver_normalize.py      # Raw endpoint payload -> canonical signal records
└── tools/
    └── quiver.py                # Typed endpoint client methods
```

### Pattern 1: Typed Quiver Endpoints Per Dataset
**What:** Give each required Quiver dataset its own request method and Pydantic response model instead of returning untyped dicts.
**When to use:** For all required datasets in `RSCH-01`.
**Example:**
```python
# Source: https://api.quiverquant.com/docs/schema.json
class CongressionalTrade(BaseModel):
    Representative: str
    Ticker: str
    Transaction: str
    ReportDate: datetime
    TransactionDate: datetime
    ExcessReturn: float | None = None


class QuiverClient:
    def get_live_congress_trading(self, ticker: str | None = None) -> list[CongressionalTrade]:
        response = self._client.get("/beta/live/congresstrading", params={"ticker": ticker} if ticker else None)
        response.raise_for_status()
        return TypeAdapter(list[CongressionalTrade]).validate_python(response.json())
```

### Pattern 2: Normalize Raw Signals Before Prompting
**What:** Convert dataset-specific shapes into a canonical per-ticker evidence bag before LLM synthesis.
**When to use:** Immediately after Quiver fetches and before prompt assembly.
**Example:**
```python
class SignalRecord(BaseModel):
    signal_type: Literal["congress", "insider", "gov_contract", "lobbying"]
    ticker: str
    observed_at: datetime
    direction: Literal["positive", "negative", "mixed", "neutral"]
    magnitude_note: str
    source_note: str


class TickerEvidenceBundle(BaseModel):
    ticker: str
    supporting_signals: list[SignalRecord]
    contradictory_signals: list[SignalRecord]
    source_summary: list[str]
```

### Pattern 3: Discriminated Structured Outcome
**What:** Validate the LLM result as one of three explicit outcomes: ranked candidates, watchlist, or no-action.
**When to use:** For the research node output contract.
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
class CandidateRecommendation(BaseModel):
    ticker: str
    action: Literal["buy", "watch"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str]
    opposing_evidence: list[str]
    risk_notes: list[str]
    source_summary: list[str]


class CandidateOutcome(BaseModel):
    outcome: Literal["candidates"]
    recommendations: list[CandidateRecommendation]


class WatchlistOutcome(BaseModel):
    outcome: Literal["watchlist"]
    summary: str
    items: list[CandidateRecommendation]


class NoActionOutcome(BaseModel):
    outcome: Literal["no_action"]
    summary: str
    reasons: list[str]


ResearchOutcome = Annotated[
    CandidateOutcome | WatchlistOutcome | NoActionOutcome,
    Field(discriminator="outcome"),
]
```

### Pattern 4: Deterministic Ranking After Validation
**What:** Score and order already-validated recommendations in Python, then prune duplicates and ineligible ideas.
**When to use:** Always, even if the LLM already returns an order.
**Example:**
```python
def rank_key(item: CandidateRecommendation) -> tuple[float, int, int, str]:
    return (
        -item.conviction_score,
        -len(item.supporting_evidence),
        len(item.opposing_evidence),
        item.ticker,
    )


def rank_candidates(items: list[CandidateRecommendation]) -> list[CandidateRecommendation]:
    deduped = dedupe_by_ticker(items)
    eligible = [item for item in deduped if is_broker_eligible(item.ticker)]
    return sorted(eligible, key=rank_key)
```

### Anti-Patterns to Avoid
- **Single-source recommendation generation:** Do not keep the current one-endpoint or one-static-response flow; it cannot satisfy `RSCH-01`.
- **LLM decides delivery mode alone:** The model can recommend watchlist/no-action, but Python should enforce thresholds for weak or conflicting evidence.
- **Ranking on raw dicts:** Quiver fields vary by endpoint and contain string amounts/dates; normalize first.
- **Implicit duplicates:** The same ticker can appear across multiple datasets and multiple rows within one dataset; collapse deterministically before delivery.
- **Prompt-only evidence:** Supporting and opposing evidence must be materialized as schema fields, not buried in free text.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Response parsing | Manual dict indexing everywhere | Pydantic models plus `TypeAdapter` validation | Quiver fields vary by endpoint and type mismatches will otherwise leak into ranking |
| Outcome branching | Ad hoc booleans like `is_watchlist` and `no_action_reason` on one model | Discriminated union outcome schema | Cleaner validation and fewer impossible state combinations |
| HTTP stubbing | Custom fake clients | `httpx.MockTransport` | Already used in repo tests and keeps adapter tests small |
| Ranking stability | Ad hoc list mutation based on prompt order | Stable Python sort with explicit tie-break key | Required for deterministic behavior in `RSCH-03` |
| Amount/date coercion | Repeated inline string parsing | Central normalization helpers | Quiver returns several business-critical values as strings |

**Key insight:** The deceptively hard part of this phase is not calling four endpoints. It is preserving determinism and explainability after combining noisy signals from heterogeneous payloads.

## Common Pitfalls

### Pitfall 1: Treating all Quiver rows as equally directional
**What goes wrong:** Government contracts and lobbying entries get treated like direct buy signals.
**Why it happens:** Different datasets imply sentiment differently; some are directional, some are contextual.
**How to avoid:** Normalize each dataset into a `direction` plus `source_note` instead of assuming every row is bullish.
**Warning signs:** Recommendations cite lobbying or contracts as standalone buy reasons without caveats.

### Pitfall 2: Letting the LLM force a candidate when evidence is weak
**What goes wrong:** The daily memo always includes at least one ticker even when signals conflict or are sparse.
**Why it happens:** Prompt wording rewards decisiveness and no deterministic threshold exists outside the prompt.
**How to avoid:** Add Python-side minimum evidence and conflict thresholds that downgrade to `watchlist` or `no_action`.
**Warning signs:** Low-conviction ideas keep appearing with thin source summaries.

### Pitfall 3: Unstable ranking due to implicit ordering
**What goes wrong:** The same input yields different rank order across runs.
**Why it happens:** Sorting relies on prompt order, dict insertion order from merged sources, or incomplete tie-breakers.
**How to avoid:** Sort on an explicit tuple and end with ticker symbol as the final tie-breaker.
**Warning signs:** Snapshot tests fail intermittently on ordering only.

### Pitfall 4: Quiver string fields bleed into business logic
**What goes wrong:** Amounts, ranges, and dates are compared lexically or not at all.
**Why it happens:** Quiver mixes numeric-looking strings with numbers across endpoints.
**How to avoid:** Parse or preserve these values centrally during normalization and never inside ranking code.
**Warning signs:** Sorts or thresholds behave strangely around large dollar amounts or dates.

### Pitfall 5: Duplicate ideas survive because only output tickers are deduped
**What goes wrong:** A ticker appears multiple times with slight rationale variation.
**Why it happens:** Deduplication is postponed until after the LLM returns multiple candidate phrasings.
**How to avoid:** Deduplicate both evidence bundles and final recommendations by canonical ticker symbol.
**Warning signs:** Email output repeats one ticker with multiple recommendation entries.

## Code Examples

Verified patterns from official sources:

### Validate JSON output directly into a model
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
response = llm.invoke(payload)
result = TypeAdapter(ResearchOutcome).validate_json(response)
```

### Use discriminated unions for explicit branches
```python
# Source: https://docs.pydantic.dev/latest/concepts/unions/
ResearchOutcome = Annotated[
    CandidateOutcome | WatchlistOutcome | NoActionOutcome,
    Field(discriminator="outcome"),
]
```

### Keep FastAPI responses schema-backed
```python
# Source: https://fastapi.tiangolo.com/tutorial/response-model/
@router.get("/runs/{run_id}", response_model=RunResearchResponse)
def get_run(run_id: str) -> Any:
    return load_run(run_id)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-source or prompt-only stock picks | Multi-signal retrieval plus structured synthesis and deterministic ranking | Current best practice in LLM application design; reinforced by modern Pydantic v2 structured validation | Better auditability and fewer forced recommendations |
| One flat recommendation schema | Discriminated outcome model with candidate/watchlist/no-action branches | Pydantic v2 era | Cleaner handling of mutually exclusive outcomes |
| SDK guesswork for third-party APIs | Typed adapter generated from or aligned to current OpenAPI | Current Quiver docs expose a usable schema at `/docs/schema.json` | Safer endpoint expansion and easier test coverage |

**Deprecated/outdated:**
- `quiverquant` as the primary integration layer for this repo: the PyPI package is current only through version `0.2.2` from 2023-06-09, while Quiver's current API docs expose broader live endpoints directly.

## Open Questions

1. **Should Phase 2 persist normalized evidence detail, or only final recommendations?**
   - What we know: Phase 1 covers durable workflow foundations, and later phases need traceability.
   - What's unclear: Whether this phase should expand database schemas now or defer persistence shape changes.
   - Recommendation: Plan the code so normalized evidence is serializable even if persistence lands in a later plan.

2. **What exact Python-side threshold should trigger watchlist or no-action?**
   - What we know: The phase requires the behavior, but no threshold is specified in repo docs.
   - What's unclear: Minimum signal count, contradiction ratio, and minimum conviction cutoff.
   - Recommendation: Put thresholds in settings and test a conservative default rather than hard-coding prompt text only.

3. **Should broker eligibility in Phase 2 call the Alpaca adapter or use a local stub/check?**
   - What we know: `RSCH-03` requires broker eligibility pruning, but Alpaca prestage is Phase 4.
   - What's unclear: Whether live broker checks are acceptable during research ranking.
   - Recommendation: Plan for an eligibility interface with a deterministic stub in tests and a pluggable real adapter later.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.2` |
| Config file | [`/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml`](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml) |
| Quick run command | `pytest tests/tools/test_clients.py tests/graph/test_research_node.py tests/services/test_risk.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSCH-01 | Fetch and type-validate congress, insiders, gov contracts, and lobbying datasets | unit | `pytest tests/tools/test_quiver_multisignal.py -q` | ❌ Wave 0 |
| RSCH-02 | Structured recommendation output contains supporting, opposing, risks, and sources | unit | `pytest tests/graph/test_research_contract.py -q` | ❌ Wave 0 |
| RSCH-03 | Deterministic ranking prunes duplicates, low conviction, and ineligible tickers | unit | `pytest tests/services/test_ranking.py -q` | ❌ Wave 0 |
| RSCH-04 | Weak/conflicting evidence yields watchlist or no-action instead of candidates | unit | `pytest tests/graph/test_research_outcomes.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/tools/test_quiver_multisignal.py tests/services/test_ranking.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/tools/test_quiver_multisignal.py` — covers `RSCH-01`
- [ ] `tests/services/test_quiver_normalize.py` — validates canonical signal conversion and string parsing
- [ ] `tests/graph/test_research_contract.py` — covers `RSCH-02`
- [ ] `tests/services/test_ranking.py` — covers `RSCH-03`
- [ ] `tests/graph/test_research_outcomes.py` — covers `RSCH-04`

## Sources

### Primary (HIGH confidence)
- Quiver API docs schema: `https://api.quiverquant.com/docs/schema.json` — verified live endpoint coverage and response schema names for congress trading, insiders, gov contracts, lobbying, house trading, and senate trading
- Quiver OpenAPI spec: `https://api.quiverquant.com/static/openapi.yaml` — verified public plugin/OpenAPI endpoint coverage and field-level descriptions
- Quiver API landing page: `https://api.quiverquant.com/` — verified current marketed datasets include Senate Trading, House Trading, Insider Trading, Government Contracts, and Corporate Lobbying
- Pydantic unions docs: `https://docs.pydantic.dev/latest/concepts/unions/` — verified discriminated union recommendation and syntax
- FastAPI response model docs: `https://fastapi.tiangolo.com/tutorial/response-model/` — verified `response_model` behavior and filtering
- PyPI JSON APIs for `fastapi`, `httpx`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, and `pytest` — verified latest package versions and publish dates

### Secondary (MEDIUM confidence)
- Quiver Quantitative Python API README: `https://raw.githubusercontent.com/Quiver-Quantitative/python-api/master/README.md` — useful for historical dataset coverage and package existence, but less authoritative than current API docs

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Current repo stack plus live PyPI version verification and official docs support
- Architecture: HIGH - Strongly constrained by existing repo shape and official Quiver/Pydantic/FastAPI docs
- Pitfalls: MEDIUM - Based on verified schema characteristics plus engineering inference from the current codebase

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
