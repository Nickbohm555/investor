---
phase: 02
slug: quiver-research-and-ranking
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-31
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.2` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/tools/test_clients.py tests/services/test_quiver_normalize.py tests/graph/test_research_node.py tests/services/test_research_prompt.py tests/services/test_ranking.py tests/services/test_email.py tests/graph/test_workflow.py tests/api/test_routes.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/tools/test_clients.py tests/services/test_quiver_normalize.py tests/graph/test_research_node.py tests/services/test_research_prompt.py tests/services/test_ranking.py tests/services/test_email.py tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | RSCH-01 | unit | `pytest tests/tools/test_clients.py -q` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | RSCH-01 | unit | `pytest tests/services/test_quiver_normalize.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | RSCH-02 | unit | `pytest tests/graph/test_research_node.py -q` | ✅ | ⬜ pending |
| 02-02-02 | 02 | 2 | RSCH-02 | unit | `pytest tests/graph/test_research_node.py tests/services/test_research_prompt.py -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | RSCH-03 | unit | `pytest tests/services/test_ranking.py -q` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 3 | RSCH-03, RSCH-04 | unit | `pytest tests/services/test_email.py tests/graph/test_workflow.py tests/api/test_routes.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_quiver_normalize.py` — normalization coverage for canonical signal conversion and ticker bundle merging
- [ ] `tests/services/test_research_prompt.py` — prompt contract coverage for discriminated research outcomes
- [ ] `tests/services/test_ranking.py` — deterministic ranking, dedupe, and downgrade rule coverage

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
