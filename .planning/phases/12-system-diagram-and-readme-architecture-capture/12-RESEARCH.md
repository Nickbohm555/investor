# Phase 12: System Diagram And README Architecture Capture - Research

**Researched:** 2026-03-31
**Domain:** Repository-truthful architecture documentation, Excalidraw diagramming, and README image integration
**Confidence:** HIGH

## User Constraints

No phase-specific `CONTEXT.md` exists for Phase 12.

Use these as the binding inputs for planning:
- `.planning/ROADMAP.md` Phase 12 goal and success criteria
- `.planning/PROJECT.md` product context and constraints
- `.planning/REQUIREMENTS.md` v1 scope and out-of-scope boundaries
- The live repo implementation and tests

## Summary

Phase 12 is a documentation phase, but it still has a real correctness boundary: the diagram must describe the runtime architecture that exists in the repository now, not the architecture the older design spec described and not the still-unimplemented submission flow planned in Phase 11. The current live system is a local-first FastAPI service with two trigger paths (`/runs/trigger` and `/runs/trigger/scheduled`), a persisted workflow engine, Quiver-backed research, SMTP memo delivery, tokenized approval links, durable run/audit storage in SQLAlchemy-backed tables, and Alpaca broker prestage after approval. The truthful end-to-end runtime currently stops at `broker_prestaged`.

For a README-facing system diagram, the planner should treat the dry-run harness and cron scripts as first-class operator proof paths, not as side notes. They are the clearest evidence of how the system is actually operated: cron invokes the scheduled route, the app dedupes by `schedule_key`, the workflow pulls Quiver data and LLM research, the memo goes to the operator inbox, approval re-enters through `/approval/{token}`, and approved recommendations generate persisted broker artifacts. Docker Compose Postgres and `.env` configuration also matter because the app is explicitly local/server installable rather than SaaS-hosted.

The best implementation slice is: first produce a source-of-truth Excalidraw asset and a diagram layout contract; then export a stable README screenshot asset and wire it into `README.md`; then add docs tests that pin the asset paths and visible architecture section so the documentation does not silently disappear or drift. Do not let this phase invent future-state arrows for order submission unless they are clearly labeled as planned and not current. The safer default is to keep the README diagram strictly about implemented runtime behavior.

**Primary recommendation:** Build one repo-owned Excalidraw source file plus one exported PNG under `docs/architecture/`, and diagram only the live runtime path through `broker_prestaged`.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Excalidraw source file | N/A repo asset | Canonical editable system diagram source | Keeps architecture edits inspectable and repeatable instead of making the README image a dead-end binary |
| PNG export from Excalidraw | N/A repo asset | README-visible screenshot of the diagram | GitHub README rendering is simplest and most reliable with a checked-in image asset |
| `README.md` | repo file | Repo entry-point orientation | Existing docs/tests already treat README as operator-facing canonical documentation |
| `pytest` | 9.0.2 | Docs regression checks for README and asset references | Existing ops/doc tests already gate README and `.env.example` drift |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI | repo dependency | Runtime entrypoint shown in the diagram | Use as the top-level app/service node because `app.main:create_app` and `app/api/routes.py` are the actual execution surface |
| SQLAlchemy + Postgres | repo dependency + Postgres 16 in compose | Durable storage lane in the diagram | Use for runs, recommendations, approval events, transitions, and broker artifacts |
| Repo cron scripts | shell scripts in `scripts/` | Automation/scheduling lane in the diagram | Use to show how scheduled execution enters the app from the operator-installed cron block |
| `python -m app.ops.dry_run` | repo command | Proof path for the architecture | Use when planning verification steps and diagram callouts because it exercises the live seams end to end with doubles |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Checked-in `.excalidraw` source + PNG export | PNG only | Faster once, but future edits become brittle and hard to maintain |
| README-only prose architecture section | No diagram | Fails the phase goal of quick orientation from the repo entry point |
| Diagramming future Phase 11 submission flow | Current runtime-only diagram | Future-state diagram is tempting, but it would be misleading because `/runs/{run_id}/execute` and submitted-order persistence do not exist yet |

**Installation:**

```bash
python -m pytest tests/ops/test_operational_docs.py -q
```

**Version verification:** `pytest` is the only implementation-time package the phase should rely on for automated verification. The repo currently declares it in `pyproject.toml`; Phase 12 should reuse the existing test stack rather than add diagram-specific tooling dependencies.

## Architecture Patterns

### Recommended Project Structure

```text
docs/
└── architecture/
    ├── system-diagram.excalidraw   # editable source of truth
    └── system-diagram.png          # README-facing export
README.md                           # embeds the PNG near the top
tests/ops/test_operational_docs.py  # asserts README and asset references
```

### Pattern 1: One Diagram, Five Lanes

**What:** Organize the diagram into five separated lanes so the architecture is legible at README scale:
1. Operator touchpoints
2. Automation and entrypoints
3. Core application/runtime
4. External services
5. Storage and durable records

**When to use:** Always. The repo already has enough moving parts that a single central blob will become unreadable.

**Example:**

```text
Operator
  -> README / dry run / cron commands
Automation
  -> cron-trigger.sh -> POST /runs/trigger/scheduled
Application
  -> FastAPI routes -> WorkflowEngine -> ResearchNode -> report/email -> approvals -> broker prestage
External
  -> Quiver API / OpenAI-compatible LLM / SMTP / Alpaca
Storage
  -> Postgres runs / recommendations / approval_events / state_transitions / broker_artifacts
```

### Pattern 2: Show Entry Paths Separately, Then Merge

**What:** Draw manual trigger, scheduled trigger, and approval callback as separate ingress arrows that converge on the same app/runtime area.

**When to use:** For truthful runtime documentation. The repo has multiple operator and automation entrypoints, and combining them into one arrow hides important control boundaries.

**Example:**

```python
# Source: app/api/routes.py
@router.post("/runs/trigger")
def trigger_run(request: Request) -> dict[str, str]:
    ...

@router.post("/runs/trigger/scheduled")
def trigger_scheduled_run(...) -> dict[str, object]:
    ...

@router.get("/approval/{token}")
def review_token(token: str, request: Request) -> dict:
    ...
```

### Pattern 3: Diagram the Persisted Workflow State, Not Just the Happy Path

**What:** The diagram should include the durable records and named workflow states that make the app restart-safe: `triggered`, `awaiting_review`, `rejected`, and `broker_prestaged`.

**When to use:** Always. The product’s core value depends on durable workflow behavior, so the storage lane is not optional decoration.

**Example:**

```python
# Source: app/workflows/engine.py
result = WorkflowResult(
    status="broker_prestaged",
    current_step="broker_prestaged",
    state_payload={...},
)
```

### Pattern 4: Use “Proof Path” Callouts

**What:** Add small callouts on the diagram or in adjacent legend text for the three most important proof surfaces:
- `python -m app.ops.dry_run`
- `./scripts/cron-install.sh` / `cron-status.sh` / `cron-trigger.sh`
- `tests/ops/test_operational_docs.py` and relevant integration tests

**When to use:** For a README-facing architecture view. It gives readers a fast path from “what is this?” to “how do I prove it works?”

### Anti-Patterns to Avoid

- **Dense center-cluster layout:** If the diagram cannot be understood in a README screenshot without zooming, it has failed the phase.
- **Future-state arrows without labels:** Do not show direct submitted-order execution as current behavior.
- **Collapsing cron into “scheduler”:** The repo explicitly uses installable cron scripts, not an internal scheduler service.
- **Treating dry run as fake architecture:** The dry-run harness is a proof path over the same runtime seams and should be acknowledged.
- **Using old LangGraph terminology:** The live repo uses `WorkflowEngine`; older specs still mention LangGraph and checkpointing.

## Recommended Plan Slices

### Slice 1: Live Architecture Inventory And Diagram Contract

Lock the component list, lane layout, asset paths, and scope boundary. The contract should explicitly name the boxes to include:
- Operator
- README / dry run / cron commands
- FastAPI service
- Routes: manual trigger, scheduled trigger, approval callback
- Workflow engine
- Research node / Quiver loop agent
- Email/report rendering
- Approval service
- Broker prestage service
- External services: Quiver, OpenAI-compatible LLM, SMTP, Alpaca
- Storage: Postgres tables and durable run state

### Slice 2: Excalidraw Source Asset

Create `docs/architecture/system-diagram.excalidraw` as the editable source of truth. The slice should include deliberate spacing, grouped sections, and a small legend for “implemented now” if needed.

### Slice 3: README Screenshot Export And Integration

Export `docs/architecture/system-diagram.png`, add a short “System Architecture” section near the top of `README.md`, embed the image with a relative path, and add 1-2 orientation sentences that match the live implementation.

### Slice 4: Drift Guards

Extend `tests/ops/test_operational_docs.py` or add a neighboring docs test to assert:
- README contains a system architecture section
- README references `docs/architecture/system-diagram.png`
- The exported PNG exists
- The editable `.excalidraw` source exists

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Diagram source management | Ad hoc screenshot edits only | Checked-in `.excalidraw` source | Makes future updates tractable and auditable |
| README image delivery | Remote image host or generated-at-view-time asset | Checked-in PNG under `docs/architecture/` | Keeps the repo self-contained and stable on GitHub and local clones |
| Architecture truth | Diagram from stale design docs | Diagram from live routes, services, scripts, and tests | Old docs still reference LangGraph and now-missing concepts |
| Documentation verification | Manual visual memory | Existing pytest docs checks | The repo already uses tests to prevent README drift |

**Key insight:** The hard part is not drawing boxes. The hard part is keeping the diagram aligned with the current runtime contract as the codebase evolves.

## Common Pitfalls

### Pitfall 1: Documenting the Original Design Instead of the Current Repo

**What goes wrong:** The diagram shows LangGraph, checkpointing, or direct submission flows that are not present in live code.

**Why it happens:** The older design specs are still in the repo and are easy to mistake for current architecture.

**How to avoid:** Treat `app/main.py`, `app/api/routes.py`, `app/workflows/engine.py`, `app/graph/workflow.py`, scripts, and tests as the primary sources of truth. Use older specs only for background.

**Warning signs:** Diagram labels mention `thread_id`, LangGraph, or submitted orders.

### Pitfall 2: Hiding the Operator Workflow

**What goes wrong:** The diagram looks technically clean but does not show how the operator actually runs or approves the system.

**Why it happens:** Engineers tend to focus on internal services and omit commands, emails, and approval links.

**How to avoid:** Give the operator lane equal visual weight. Show cron install/status, dry run, daily memo inbox, and approval-link click path.

**Warning signs:** No operator box, no memo inbox, or no approval callback arrow.

### Pitfall 3: Overcompressing the Storage Layer

**What goes wrong:** Postgres appears as a single generic cylinder with no explanation of what is persisted.

**Why it happens:** Documentation phases often flatten persistence details to save space.

**How to avoid:** Label the durable records inside or next to the storage node: runs, recommendations, approval events, transitions, broker artifacts.

**Warning signs:** The reader cannot tell why the system is restart-safe.

### Pitfall 4: README Screenshot Drift

**What goes wrong:** The Excalidraw source is updated later, but the PNG in README is not.

**Why it happens:** Source and export are separate files and there is no built-in guard.

**How to avoid:** Store both files side by side, document the export contract in the plan, and add tests that at least require both assets to exist and README to reference the PNG.

**Warning signs:** `.excalidraw` exists but README still points at a missing or old image path.

## Code Examples

Verified repo patterns from live sources:

### Manual And Scheduled Trigger Surfaces

```python
# Source: app/api/routes.py
@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    ...

@router.post("/runs/trigger/scheduled")
def trigger_scheduled_run(...) -> dict[str, object]:
    ...
```

### Approval Callback Surface

```python
# Source: app/api/routes.py
@router.get("/approval/{token}")
def review_token(token: str, request: Request) -> dict:
    ...
```

### README Image Embed Pattern

```markdown
## System Architecture

![Investor system architecture](docs/architecture/system-diagram.png)

The current runtime flow is cron or manual trigger -> FastAPI workflow execution -> daily memo -> approval callback -> Alpaca broker prestage.
```

### Dry-Run Proof Path

```bash
# Source: README.md and app/ops/dry_run.py
python -m app.ops.dry_run
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangGraph/checkpointer architecture in specs | App-owned `WorkflowEngine` plus SQLAlchemy-backed persisted state | Phase 6, completed 2026-03-31 | Diagram must reflect app-owned orchestration, not LangGraph |
| Recommendation email framing only | Strategic insight report rendering with text and HTML templates | Phase 8, completed 2026-03-31 | Diagram should show report/email rendering as a distinct component |
| Architecture hidden in phase docs only | README-visible architecture image | Phase 12 target | New contributors and operators get orientation from the repo entry point |

**Deprecated/outdated:**
- `docs/specs/2026-03-30-investor-design.md`: useful for intent, but outdated on workflow engine details.
- `docs/superpowers/specs/2026-03-30-investor-design.md`: same issue; still references LangGraph-era architecture.

## Open Questions

1. **Should the diagram include planned Phase 11 submission work?**
   - What we know: The roadmap makes Phase 12 depend on Phase 11, but the live repo today still ends at `broker_prestaged`.
   - What's unclear: Whether planning will happen before or after Phase 11 implementation lands.
   - Recommendation: Default to current-state-only documentation. If Phase 11 completes first, update the component inventory before drawing.

2. **Should the README show the full-size exported diagram or a cropped screenshot?**
   - What we know: The roadmap explicitly asks for a screenshot in the README and the layout must remain highly legible.
   - What's unclear: The optimal dimensions for GitHub README viewing.
   - Recommendation: Export one full PNG sized for horizontal readability first. Only introduce a second cropped asset if the full PNG becomes unreadable in README.

3. **How much table-level storage detail belongs in the diagram itself?**
   - What we know: Restart-safe persistence is central to understanding the system.
   - What's unclear: Whether listing every table inside the main diagram hurts readability.
   - Recommendation: Show the five durable record types in or beside the Postgres node, not as separate first-class boxes unless space allows cleanly.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` (repo-declared) |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/ops/test_operational_docs.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC12-01 | Diagram asset exists and covers the live runtime architecture surface | docs/unit | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ Wave 0 |
| SC12-02 | README embeds the exported screenshot from a stable repo path | docs/unit | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ Wave 0 |
| SC12-03 | Diagram and README remain aligned with the current implementation scope | manual + docs/unit | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ops/test_operational_docs.py -q`
- **Per wave merge:** `python -m pytest tests/ops/test_operational_docs.py tests/ops/test_dry_run.py -q`
- **Phase gate:** `python -m pytest -q`

### Wave 0 Gaps

- [ ] Extend `tests/ops/test_operational_docs.py` to assert a README architecture section and image reference.
- [ ] Add existence checks for `docs/architecture/system-diagram.excalidraw` and `docs/architecture/system-diagram.png`.
- [ ] Add a manual verification note to the plan for legibility at README scale because automated tests cannot judge spacing quality.

## Sources

### Primary (HIGH confidence)

- Live repo source files:
  - `app/main.py`
  - `app/api/routes.py`
  - `app/workflows/engine.py`
  - `app/graph/workflow.py`
  - `app/services/approvals.py`
  - `app/services/broker_prestage.py`
  - `app/tools/quiver.py`
  - `app/tools/alpaca.py`
  - `app/config.py`
  - `app/db/models.py`
  - `app/ops/dry_run.py`
  - `scripts/cron-install.sh`
  - `scripts/cron-status.sh`
  - `scripts/cron-trigger.sh`
  - `README.md`
- Live verification and docs tests:
  - `tests/ops/test_dry_run.py`
  - `tests/ops/test_operational_docs.py`
  - `tests/ops/test_cron_scripts.py`
  - `tests/integration/test_hitl_resume.py`
  - `tests/integration/test_broker_prestage.py`

### Secondary (MEDIUM confidence)

- `.planning/ROADMAP.md` - Phase 12 target scope and success criteria
- `.planning/PROJECT.md` - product context and constraints
- `.planning/phases/11-scheduling-reliability-and-end-to-end-execution-proof/11-RESEARCH.md` - future-state warning for still-missing submission behavior

### Tertiary (LOW confidence)

- `docs/specs/2026-03-30-investor-design.md` - original product intent, but stale on orchestration details
- `docs/superpowers/specs/2026-03-30-investor-design.md` - same stale architecture issue

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Phase 12 should reuse repo-native assets, README, and pytest instead of introducing uncertain tooling.
- Architecture: HIGH - The runtime flow is directly supported by live routes, services, scripts, and integration tests.
- Pitfalls: HIGH - The main risks are repo-specific and were confirmed by comparing live code against older stale design docs.

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 unless Phase 11 implementation lands first
