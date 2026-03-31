---
phase: 08
slug: upgrade-outputs-to-strategic-insight-reports
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-31
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.1.2 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/services/test_report_compare.py tests/services/test_report_builder.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local verify command from the map below
- **After every plan wave:** Run `python -m pytest tests/graph/test_workflow_reporting.py tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | SC-08-01 | unit | `python -m pytest tests/services/test_report_compare.py -q` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | SC-08-01 | unit | `python -m pytest tests/services/test_report_builder.py -q` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | SC-08-02 | unit | `python -m pytest tests/services/test_report_render.py -q` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | SC-08-02 | unit | `python -m pytest tests/services/test_email.py tests/services/test_report_render.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 3 | SC-08-03 | unit/integration | `python -m pytest tests/graph/test_workflow_reporting.py tests/graph/test_workflow.py -q` | ❌ W0 / ✅ existing | ⬜ pending |
| 08-03-02 | 03 | 3 | SC-08-03 | integration | `python -m pytest tests/api/test_routes.py tests/graph/test_workflow_reporting.py -q` | ✅ existing / ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_report_compare.py` — proves previous-run diff logic and stable change labels
- [ ] `tests/services/test_report_builder.py` — proves bucket classification and uncertainty/research-gap handling
- [ ] `tests/services/test_report_render.py` — proves deterministic text/HTML output and template-required fields
- [ ] `tests/services/test_email.py` — proves report-email wrapper delegates to the deterministic renderer
- [ ] `tests/graph/test_workflow_reporting.py` — proves workflow uses the new builder/renderer seam instead of the old flat memo path

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
