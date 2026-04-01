---
phase: 12
slug: system-diagram-and-readme-architecture-capture
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-31
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 installed in repo environment |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/ops/test_operational_docs.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `<automated>` command from the active plan
- **After every plan wave:** Run `python -m pytest tests/ops/test_operational_docs.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | ARCH-01 | docs-contract | `rg -n "Operator|Automation|Application Runtime|External Services|Storage|/runs/trigger|/runs/trigger/scheduled|/approval/\\{token\\}|WorkflowEngine|ResearchNode|compose_report_email|BrokerPrestageService|broker_prestaged|python -m app.ops.dry_run|./scripts/cron-install.sh|./scripts/cron-trigger.sh|Quiver|OpenAI-compatible LLM|SMTP|Alpaca|runs|recommendations|approval_events|state_transitions|broker_artifacts" docs/architecture/system-diagram-contract.md` | ❌ pending | ⬜ pending |
| 12-01-02 | 01 | 1 | ARCH-02 | asset-content | `rg -n "Operator|Automation|Application Runtime|External Services|Storage|Manual trigger|Scheduled trigger|Approval callback|WorkflowEngine|ResearchNode|SMTP memo|broker_prestaged|runs|recommendations|approval_events|state_transitions|broker_artifacts|python -m app.ops.dry_run|./scripts/cron-install.sh|./scripts/cron-trigger.sh" docs/architecture/system-diagram.excalidraw docs/architecture/system-diagram-contract.md` | ❌ pending | ⬜ pending |
| 12-02-01 | 02 | 2 | ARCH-03 | docs-tests | `python -m pytest tests/ops/test_operational_docs.py -q` | ✅ existing test file | ⬜ pending |
| 12-02-02 | 02 | 2 | ARCH-03 | docs-tests | `python -m pytest tests/ops/test_operational_docs.py -q` | ✅ existing test file | ⬜ pending |
| 12-02-03 | 02 | 2 | ARCH-03 | visual-checkpoint | Human verify README preview and screenshot legibility | ❌ output asset pending | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None. The existing docs test module is already present; Phase 12 extends it instead of requiring brand-new verification scaffolding.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The exported screenshot is readable at normal README preview scale | ARCH-02, ARCH-03 | Automated checks can prove assets and references exist, but not whether the rendered image is visually legible and well spaced | Preview `README.md`, confirm the architecture image is visible near the top, the lane layout is readable without zooming, and no boxes or labels overlap |
| The diagram stays truthful to the current runtime boundary | ARCH-01, ARCH-03 | Text checks can require key phrases, but a human should confirm the visual flow does not imply direct order submission or old LangGraph semantics | Inspect the diagram and README copy, verify the approved path ends at `broker_prestaged`, and confirm there are no current-state labels for submitted orders or LangGraph |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or a structured checkpoint
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 75s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
