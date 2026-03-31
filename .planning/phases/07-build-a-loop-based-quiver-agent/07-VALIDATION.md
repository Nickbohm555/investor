---
phase: 07
slug: build-a-loop-based-quiver-agent
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-31
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/services/test_research_prompt.py tests/services/test_research_llm.py tests/agents/test_quiver_loop.py -q` |
| **Full phase command** | `pytest tests/services/test_research_prompt.py tests/services/test_research_llm.py tests/agents/test_quiver_loop.py tests/graph/test_research_node.py tests/graph/test_workflow.py tests/api/test_routes.py tests/ops/test_readiness.py tests/ops/test_dry_run.py -q` |
| **Estimated runtime** | ~25-40 seconds for phase checks once implemented |

---

## Sampling Rate

- **After 07-01 Task 1 commit:** Run `pytest tests/services/test_research_prompt.py -q`
- **After 07-01 Task 2 commit:** Run `pytest tests/services/test_research_llm.py -q`
- **After 07-02 Task 1 commit:** Run `pytest tests/agents/test_quiver_loop.py -q`
- **After 07-02 Task 2 commit:** Run `pytest tests/graph/test_research_node.py tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **After 07-03 Task 1 commit:** Run `pytest tests/ops/test_readiness.py tests/services/test_research_llm.py -q`
- **After 07-03 Task 2 commit:** Run `pytest tests/ops/test_dry_run.py -q`
- **After every plan wave:** Run the full phase command above
- **Before `$gsd-verify-work`:** Run `pytest -q`
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | AGENT-01 | unit | `pytest tests/services/test_research_prompt.py -q` | ✅ planned | ⬜ pending |
| 07-01-02 | 01 | 1 | AGENT-01 | unit | `pytest tests/services/test_research_llm.py -q` | ✅ planned | ⬜ pending |
| 07-02-01 | 02 | 2 | AGENT-01 | unit | `pytest tests/agents/test_quiver_loop.py -q` | ✅ planned | ⬜ pending |
| 07-02-02 | 02 | 2 | AGENT-02, AGENT-03 | integration | `pytest tests/graph/test_research_node.py tests/graph/test_workflow.py tests/api/test_routes.py -q` | ✅ planned | ⬜ pending |
| 07-03-01 | 03 | 3 | AGENT-01 | unit/integration | `pytest tests/ops/test_readiness.py tests/services/test_research_llm.py -q` | ✅ planned | ⬜ pending |
| 07-03-02 | 03 | 3 | AGENT-03 | smoke/integration | `pytest tests/ops/test_dry_run.py -q` | ✅ planned | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] No Wave 0 scaffold tasks required. Every planned task already has a concrete automated verification command.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `python -m app.ops.dry_run` emits operator-readable loop metadata while still ending at `broker_prestaged` | AGENT-03 | Final operator smoke check after automated dry-run coverage | Run the command once after `07-03`; confirm JSON includes `research_tool_call_count`, `research_stop_reason`, and `investigated_tickers` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verification commands
- [x] Sampling continuity keeps feedback after each task commit
- [x] Wave 0 is complete because no missing verification scaffolds remain
- [x] No watch-mode or manual-only execution dependencies are required
- [ ] Mark task statuses green during execution

**Approval:** pending
