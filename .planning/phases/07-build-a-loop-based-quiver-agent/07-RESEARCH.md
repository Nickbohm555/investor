# Phase 7: Build A Loop-Based Quiver Agent - Research

**Researched:** 2026-03-31
**Domain:** Bounded tool-using research agents over Quiver evidence in the existing Python/FastAPI stack
**Confidence:** MEDIUM

## User Constraints

- No `CONTEXT.md` exists for Phase 7, so plan from roadmap, requirements, state, and current code only.
- Treat the Go repo as lightweight inspiration, not canonical product scope.
- Keep the existing Python/FastAPI/Postgres direction and reuse the current repository shape instead of replatforming.
- Phase 7 follows Phase 6, so the plan should target app-owned workflow/runtime seams rather than deepen LangGraph coupling.

## Summary

Phase 7 should not introduce a third-party agent framework. The repo already injects research behavior cleanly at `app.state.research_node`, and Phase 6 explicitly aims to remove LangGraph-era semantics rather than replace them with another orchestration dependency. The standard implementation for this phase is an app-owned serial tool loop: the model receives a small set of strictly defined Quiver tools, chooses the next inspection step, the application executes the call, appends the result plus a trace entry, and repeats until a stop condition is met or a hard budget is exhausted.

The current one-shot flow fetches all four Quiver datasets up front, normalizes them, and asks the LLM for a single JSON answer. That preserves deterministic ranking but loses adaptivity and traceability. The loop agent should keep deterministic post-processing exactly where it is now: `finalize_research_outcome()` remains the authority for pruning, ranking, watchlist downgrade, and no-action fallback. The agent's job becomes evidence gathering and synthesis, not final business policy.

The most important planning decision is scope of tool calls. Do not let the agent repeatedly scan unbounded global feeds. Use one deterministic broad-scan seed step to identify candidate tickers or theses, then expose ticker-scoped Quiver follow-up tools for bounded investigation. Persist each thought-free trace step as structured metadata in run state so restart-safe workflow behavior and operator auditability survive the shift from one pass to a loop.

**Primary recommendation:** Build a repo-local `QuiverLoopAgent` that runs a serial, max-step, max-tool-call loop over strict Quiver tool schemas, persists trace steps in `state_payload`, and still returns the existing `ResearchOutcome` union for downstream ranking and delivery.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | `0.135.2` | Existing app/runtime composition | Already owns dependency injection, app state, and route boundaries in this repo |
| `httpx` | `0.28.1` | Reusable HTTP client for LLM and Quiver adapters | Keeps external I/O at the edge and already supports repo test doubles via `MockTransport` |
| `pydantic` | `2.12.5` | Tool argument models, trace models, and final `ResearchOutcome` validation | Current repo pattern; discriminated unions and `TypeAdapter` fit tool-loop contracts well |
| `pydantic-settings` | `2.13.1` | Agent budget/provider capability settings | Existing env-backed config mechanism |
| `sqlalchemy` | `2.0.48` | Persisting trace state inside run records | Current durable run state already flows through SQLAlchemy-backed services |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `9.0.2` | Loop, trace, and workflow regression coverage | For new unit/integration tests around bounded loops and persisted traces |
| `alembic` | `1.18.4` | Schema migration only if traces move out of `runs.state_payload` into first-class tables | Use only if JSON payload storage proves insufficient for operator review needs |
| `openai` | `2.30.0` | Optional future SDK if product commits to OpenAI-only APIs | Only use if portability to OpenAI-compatible providers is intentionally dropped |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| App-owned loop executor | OpenAI Agents SDK | Faster bootstrap, but adds framework coupling and assumes narrower provider/API choices than the current OpenAI-compatible adapter seam |
| Chat Completions + app-owned loop | Responses API + official SDK | More agent-native if the product standardizes on OpenAI, but weaker fit for today's provider-agnostic `base_url` design |
| Serial tool execution | Model-directed parallel tool calls | Lower latency in theory, but harder to trace, budget, and replay deterministically for this phase |

**Installation:**
```bash
# No new dependency is required for the recommended Phase 7 approach.
# Keep the existing stack unless Phase 7 explicitly chooses OpenAI-only APIs.
```

**Version verification:** Verified against PyPI on 2026-03-31.
- `fastapi` `0.135.2` — published 2026-03-23
- `httpx` `0.28.1` — published 2024-12-06
- `pydantic` `2.12.5` — published 2025-11-26
- `pydantic-settings` `2.13.1` — published 2026-02-19
- `sqlalchemy` `2.0.48` — published 2026-03-02
- `alembic` `1.18.4` — published 2026-02-10
- `pytest` `9.0.2` — published 2025-12-06
- `openai` `2.30.0` — published 2026-03-25

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── agents/
│   ├── research.py                  # Keep thin workflow-facing interface
│   └── quiver_loop.py               # New bounded loop executor
├── schemas/
│   ├── quiver.py                    # Existing Quiver row/evidence models
│   ├── research.py                  # Existing final outcome contract
│   └── research_agent.py            # New tool-call, trace, and budget models
├── services/
│   ├── research_llm.py              # Extend to support tool calls/messages
│   ├── research_prompt.py           # Replace one-shot prompt builder with loop system prompt + final synthesis prompt
│   ├── quiver_normalize.py          # Keep deterministic normalization helpers
│   └── research_trace.py            # Trace serialization helpers for state payload persistence
└── tools/
    └── quiver.py                    # Keep typed adapter; add narrow ticker-scoped methods only if needed
```

### Pattern 1: App-Owned Serial Tool Loop
**What:** The application owns the loop state, executes one tool decision at a time, records the result, and decides whether another model turn is allowed.
**When to use:** For every research run in Phase 7.
**Example:**
```python
# Source: repo architecture + OpenAI function calling guide
class QuiverLoopAgent:
    def run(self, *, run_id: str, seed: SeedUniverse, account_context: dict[str, str]) -> ResearchOutcome:
        transcript = self._bootstrap_messages(run_id, seed, account_context)
        trace: list[AgentTraceStep] = []

        for step_index in range(self._settings.max_agent_steps):
            assistant = self._llm.complete_with_tools(
                messages=transcript,
                tools=self._tool_registry.definitions(),
                tool_choice="auto",
                parallel_tool_calls=False,
            )
            decision = self._parse_assistant_turn(assistant, step_index=step_index)
            trace.append(decision.trace_step)

            if decision.kind == "final":
                return TypeAdapter(ResearchOutcome).validate_python(decision.payload)

            tool_result = self._tool_registry.execute(decision.tool_name, decision.arguments)
            transcript.extend(self._append_tool_exchange(assistant, tool_result))

        raise AgentBudgetExceeded(f"Exceeded {self._settings.max_agent_steps} agent steps")
```

### Pattern 2: Deterministic Seed, Then Targeted Follow-Ups
**What:** Start with one broad deterministic seed pass over Quiver feeds, derive a bounded candidate set, then allow the agent to inspect ticker-scoped follow-ups.
**When to use:** Whenever the underlying Quiver endpoints can return large global result sets.
**Example:**
```python
class SeedUniverse(BaseModel):
    ranked_tickers: list[str]
    seed_reasons: dict[str, list[str]]


def build_seed_universe(quiver: QuiverClient) -> SeedUniverse:
    bundles = build_ticker_evidence_bundles(
        congress=quiver.get_live_congress_trading(),
        insiders=quiver.get_live_insider_trading(),
        gov_contracts=quiver.get_live_government_contracts(),
        lobbying=quiver.get_live_lobbying(),
    )
    ranked = sorted(
        bundles,
        key=lambda bundle: (-len(bundle.supporting_signals), len(bundle.contradictory_signals), bundle.ticker),
    )
    return SeedUniverse(
        ranked_tickers=[bundle.ticker for bundle in ranked[:10]],
        seed_reasons={bundle.ticker: bundle.source_summary[:3] for bundle in ranked[:10]},
    )
```

### Pattern 3: Strict Tool Argument Models
**What:** Define each callable tool with a Pydantic request model and generate JSON Schema from that model.
**When to use:** For all Quiver tool calls.
**Example:**
```python
# Source: https://developers.openai.com/api/docs/guides/function-calling
class TickerLookupArgs(BaseModel):
    ticker: str = Field(min_length=1, description="Uppercase ticker symbol to inspect")
    dataset: Literal["congress", "insider", "gov_contracts", "lobbying"]
    rationale: str = Field(
        min_length=5,
        description="Why this extra lookup is useful for the current thesis",
    )


tool_definition = {
    "type": "function",
    "name": "lookup_quiver_ticker",
    "description": "Fetch one Quiver dataset for one ticker when more evidence is needed.",
    "parameters": TickerLookupArgs.model_json_schema(),
    "strict": True,
}
```

### Pattern 4: Persist Trace As Structured State, Not Prompt Text
**What:** Store loop decisions and tool results as typed trace items in `RunRecord.state_payload`.
**When to use:** Always; success criteria require research traces.
**Example:**
```python
class AgentTraceStep(BaseModel):
    step_index: int
    action: Literal["tool_call", "finalize", "stop"]
    rationale: str
    tool_name: str | None = None
    tool_args: dict[str, object] = Field(default_factory=dict)
    result_summary: str | None = None


state["research_trace"] = [step.model_dump(mode="python") for step in trace]
run_service.store_state_payload(run_id, state)
```

### Pattern 5: Final Output Remains Backward-Compatible
**What:** The agent may gather evidence iteratively, but it still emits the existing `ResearchOutcome` discriminated union before ranking.
**When to use:** For every successful agent completion.
**Example:**
```python
raw_outcome = loop_agent.run(
    run_id=state["run_id"],
    seed=seed_universe,
    account_context={"buying_power": state["buying_power"]},
)
finalized_outcome = finalize_research_outcome(raw_outcome)
```

### Anti-Patterns to Avoid
- **Tool loop inside the prompt only:** Do not ask the model to "simulate" extra investigation without real tool execution and persisted trace rows.
- **Repeated global-feed scans:** Broad Quiver endpoints without ticker filters should not be callable on every turn.
- **Parallel tool calls by default:** They make trace ordering, budget accounting, and replay behavior harder for little gain in this repo.
- **Business policy in the loop agent:** Broker eligibility, pruning, and watchlist/no-action downgrade must stay deterministic in Python after agent output validation.
- **Provider lock-in by accident:** Do not move to an OpenAI-only SDK/API unless the phase explicitly decides to abandon the current OpenAI-compatible base URL seam.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool argument parsing | Ad hoc `json.loads()` plus dict indexing | Pydantic request models + generated JSON Schema | Keeps tool contracts explicit and validates bad arguments early |
| Final outcome validation | Manual branch checks on raw JSON | Existing `ResearchOutcome` discriminated union | Already matches ranking/email/workflow expectations |
| HTTP-layer fakes | Custom socket or monkeypatch machinery | `httpx.MockTransport` | Already standard in this repo for Quiver and LLM tests |
| Trace persistence format | Free-form strings in email/body or logs only | Typed `AgentTraceStep` objects serialized into `state_payload` | Needed for restart safety and later operator review |
| Candidate ordering | Agent-produced order | Existing `finalize_research_outcome()` and stable rank key | Preserves deterministic RSCH behavior after the loop is introduced |

**Key insight:** The hard part of this phase is not "make the model call tools." It is keeping the loop bounded, replayable, testable, and provider-portable while preserving the deterministic downstream contract.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `runs.state_payload` already stores `evidence_bundles`, `finalized_outcome`, and `recommendations`; awaiting-review runs may outlive deploys | Code edit for new runs to add `research_trace` and any seed metadata. No mandatory data migration if old paused runs are allowed to finish with missing trace fields. If mixed-version in-flight research runs must resume mid-loop, add backward-compatible readers for absent trace/budget keys |
| Live service config | None found beyond repo-managed env settings and cron invoking HTTP routes; no external UI-managed agent config was found in repo docs | None verified from repo. Plan only needs env/docs changes if new loop budgets become configurable |
| OS-registered state | Cron scripts trigger routes but do not encode one-shot research semantics or agent names | None; code edit only |
| Secrets/env vars | Existing OpenAI-compatible envs (`base_url`, `api_key`, `model`) remain the seam; provider capability for tool calling/strict structured outputs is not guaranteed by the repo today | Code edit and readiness validation only. No key rename. Add startup or dry-run capability probe if Phase 7 depends on tool calling |
| Build artifacts | None repo-specific beyond normal Python environment installs; no generated artifact currently embeds one-shot research behavior | None verified from repo |

## Common Pitfalls

### Pitfall 1: Letting the agent rescan the full universe each turn
**What goes wrong:** Token cost, latency, and duplicate evidence explode, and traces become hard to interpret.
**Why it happens:** Global feed endpoints are easy to expose as tools because they already exist.
**How to avoid:** Run one deterministic seed pass, then expose only bounded ticker-scoped or seed-scoped follow-up tools.
**Warning signs:** Trace logs show the same four untickered Quiver calls on multiple steps.

### Pitfall 2: Mixing agent reasoning with deterministic ranking policy
**What goes wrong:** Final output order and watchlist/no-action behavior become non-repeatable.
**Why it happens:** The loop feels like a natural place to let the model rank what it found.
**How to avoid:** Keep the current Python-side `finalize_research_outcome()` flow after final validation.
**Warning signs:** Same trace yields different candidate order or branch selection across runs.

### Pitfall 3: Depending on provider features the configured base URL may not support
**What goes wrong:** The app works against OpenAI proper but fails against another OpenAI-compatible endpoint.
**Why it happens:** Tool calling, `strict` schemas, and `json_schema` support vary across providers.
**How to avoid:** Plan a Wave 0 capability check and keep a compatibility fallback such as `json_object` final output if strict schemas are unsupported.
**Warning signs:** Dry run passes with mocks but live startup fails on first tool-enabled call.

### Pitfall 4: Treating traces as debug logs instead of product state
**What goes wrong:** Restart-safe runs lose the explanation of why extra evidence was fetched.
**Why it happens:** It is tempting to write traces to stdout only.
**How to avoid:** Persist trace steps in `state_payload` or a dedicated table as part of the workflow state update path.
**Warning signs:** Approval-time state has final recommendations but no inspectable investigation history.

### Pitfall 5: Parallel tool calls without deterministic merge rules
**What goes wrong:** The same run yields different trace ordering and different synthesized summaries.
**Why it happens:** Some providers can emit multiple tool calls in one assistant turn.
**How to avoid:** Disable parallel tool calls for Phase 7 and keep one call per turn.
**Warning signs:** Tests need order-insensitive assertions for trace steps that should be stable.

### Pitfall 6: No explicit stop reason taxonomy
**What goes wrong:** A run ends, but nobody can tell whether it stopped because evidence was sufficient, budget was exhausted, or no ticker survived.
**Why it happens:** The first implementation often just stops when the model returns final JSON.
**How to avoid:** Persist a stop reason enum such as `final_answer`, `budget_exhausted`, `no_more_candidates`, or `provider_capability_missing`.
**Warning signs:** Operator or tests can only infer stop conditions indirectly from free text.

## Code Examples

Verified patterns from official sources:

### Strict function tool definition
```python
# Source: https://developers.openai.com/api/docs/guides/function-calling
tool = {
    "type": "function",
    "name": "lookup_quiver_ticker",
    "description": "Fetch one Quiver dataset for a single ticker.",
    "parameters": TickerLookupArgs.model_json_schema(),
    "strict": True,
}
```

### Strict structured final output when provider supports it
```python
# Source: https://developers.openai.com/api/docs/guides/structured-outputs
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "research_outcome",
        "schema": TypeAdapter(ResearchOutcome).json_schema(),
        "strict": True,
    },
}
```

### Validate final output into the existing discriminated union
```python
# Source: https://docs.pydantic.dev/latest/concepts/json/
result = TypeAdapter(ResearchOutcome).validate_json(raw_json)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| One-shot prompt over a prebuilt evidence bundle | Serial tool-calling loop with app-owned budgets and trace persistence | 2024-2026 ecosystem shift toward tool-calling/agent APIs | Better adaptivity and inspectability, but only if the loop is bounded and persisted |
| `response_format={"type":"json_object"}` only | Strict schema-based outputs when provider support exists | OpenAI docs now recommend `json_schema` + `strict: true` for structured outputs | Stronger final-shape guarantees, but portability must be verified before adopting as a hard dependency |
| Framework-owned orchestration | App-owned workflow + app-owned agent loop | This repo's Phase 6/7 direction | Keeps restart safety and product behavior in repo code instead of opaque framework state |

**Deprecated/outdated:**
- Giant free-text research prompts with no real tool execution are outdated for this phase's success criteria because they cannot produce trustworthy investigation traces.
- Treating the model's returned order as final is outdated in this repo because deterministic ranking/pruning is already a deliberate architectural decision from Phase 2.

## Open Questions

1. **Which provider capabilities are guaranteed at the configured `openai_base_url`?**
   - What we know: The repo currently posts Chat Completions JSON to an OpenAI-compatible endpoint and only asserts `json_object` output in tests.
   - What's unclear: Whether the real provider supports tool calling, `strict` tool schemas, `parallel_tool_calls`, and strict `json_schema` outputs.
   - Recommendation: Add a Wave 0 capability probe and plan a compatibility fallback.

2. **Should trace history stay in `runs.state_payload` or move to a first-class table?**
   - What we know: Existing durable workflow state already survives in `state_payload`, and success criteria only require traces to exist.
   - What's unclear: Whether future operator-facing report views in Phase 8 need queryable per-step trace rows.
   - Recommendation: Start in `state_payload` for Phase 7; only add a table if Phase 8 reporting/query needs make it necessary.

3. **What is the exact post-Phase-6 runtime seam?**
   - What we know: Phase 7 depends on Phase 6 and should not deepen LangGraph coupling.
   - What's unclear: Whether the workflow entry point still calls `research_node.run(...)` directly or shifts to a different app-owned runtime contract.
   - Recommendation: Plan Phase 7 against the narrowest seam possible: one injected research agent returning `ResearchOutcome` plus trace metadata.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.2` |
| Config file | [`pyproject.toml`](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml) |
| Quick run command | `python -m pytest tests/graph/test_research_node.py tests/services/test_research_llm.py tests/graph/test_workflow.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC7-1 | Agent can make multiple Quiver tool calls in one run with explicit stop conditions and budget limits | unit | `python -m pytest tests/agents/test_quiver_loop.py -q` | ❌ Wave 0 |
| SC7-2 | Research traces show why the agent chose additional investigation steps | unit | `python -m pytest tests/services/test_research_trace.py -q` | ❌ Wave 0 |
| SC7-3 | Final recommendations still satisfy candidate/watchlist/no-action contract after looping | unit | `python -m pytest tests/graph/test_research_node.py tests/graph/test_workflow.py -q` | ✅ |
| SC7-4 | Persisted runs retain trace metadata across restart-safe workflow behavior | integration | `python -m pytest tests/integration/test_loop_research_resume.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/agents/test_quiver_loop.py tests/services/test_research_trace.py tests/graph/test_workflow.py -q`
- **Per wave merge:** `python -m pytest tests/graph/test_research_node.py tests/services/test_research_llm.py tests/graph/test_workflow.py tests/integration/test_loop_research_resume.py -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/agents/test_quiver_loop.py` — covers bounded loop execution, max-step/max-tool-call stop reasons, and serial tool execution
- [ ] `tests/services/test_research_trace.py` — covers trace serialization and persistence shape
- [ ] `tests/integration/test_loop_research_resume.py` — covers persisted trace visibility and restart-safe workflow compatibility
- [ ] LLM capability-double fixtures in `tests/conftest.py` — cover tool-calling responses, final structured responses, and unsupported-provider fallback

## Sources

### Primary (HIGH confidence)
- OpenAI Function Calling guide — tool definition shape, JSON Schema-backed parameters, and strict mode: https://developers.openai.com/api/docs/guides/function-calling
- OpenAI Structured Outputs guide — `json_schema` response format and `strict: true`: https://developers.openai.com/api/docs/guides/structured-outputs
- Pydantic JSON validation docs — `TypeAdapter.validate_json` and partial JSON notes: https://docs.pydantic.dev/latest/concepts/json/
- Pydantic unions docs — discriminated unions for explicit branch models: https://docs.pydantic.dev/latest/concepts/unions/
- Current repo code: [`app/agents/research.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/agents/research.py), [`app/graph/workflow.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py), [`app/services/research_llm.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/services/research_llm.py), [`app/services/quiver_normalize.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/services/quiver_normalize.py), [`app/db/models.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/db/models.py)

### Secondary (MEDIUM confidence)
- HTTPX advanced client guidance — reusable client pattern aligns with current adapter design: https://www.python-httpx.org/advanced/clients/
- Phase 2 prior research — deterministic ranking and evidence normalization constraints that Phase 7 must preserve: [`02-RESEARCH.md`](/Users/nickbohm/Desktop/Tinkering/investor/.planning/phases/02-quiver-research-and-ranking/02-RESEARCH.md)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Mostly existing repo stack with verified package versions and no mandatory new dependency
- Architecture: MEDIUM - Strongly supported by repo seams and official tool-calling docs, but exact Phase 6 seam is not implemented yet
- Pitfalls: MEDIUM - Derived from current repo constraints plus official structured output/tool-call limitations, but live provider behavior is still unverified

**Research date:** 2026-03-31
**Valid until:** 2026-04-07
