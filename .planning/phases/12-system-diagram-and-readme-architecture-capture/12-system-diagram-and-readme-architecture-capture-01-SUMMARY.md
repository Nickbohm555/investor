---
phase: 12-system-diagram-and-readme-architecture-capture
plan: 01
subsystem: docs
tags: [architecture, docs, excalidraw, readme, workflow, runtime]
requires:
  - phase: 11-scheduling-reliability-and-end-to-end-execution-proof
    provides: scheduled trigger, approval, and broker-prestage runtime seams
provides:
  - architecture inventory contract for the live runtime
  - editable Excalidraw system diagram source
  - repo-owned diagram source aligned to the broker_prestaged boundary
affects: [readme, docs, operations]
tech-stack:
  added: []
  patterns:
    - contract-first architecture assets keep the README export derived from one editable source
key-files:
  created:
    - docs/architecture/system-diagram-contract.md
    - docs/architecture/system-diagram.excalidraw
  modified: []
key-decisions:
  - "The architecture contract and diagram intentionally stop at broker_prestaged so the README view stays truthful to the approved-path runtime instead of implying current direct submission."
  - "The system diagram uses five vertically stacked lanes with proof-path callouts so the export remains inspectable at README scale."
patterns-established:
  - "Architecture diagram changes start in docs/architecture/system-diagram-contract.md, then flow into docs/architecture/system-diagram.excalidraw."
requirements-completed: [ARCH-01, ARCH-02]
duration: 6min
completed: 2026-04-01
---

# Phase 12: System Diagram And README Architecture Capture Summary

**The repo now owns a contract-first architecture diagram source that shows the live trigger, approval, runtime, external-service, and storage surfaces through `broker_prestaged`.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-01T01:20:08Z
- **Completed:** 2026-04-01T01:27:18Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Locked the live architecture inventory, lane order, proof paths, and required edges into a markdown contract.
- Built a repo-owned Excalidraw source asset that reflects the implemented runtime instead of the stale LangGraph-era design.
- Preserved a deliberately spaced diagram layout with visible operator, automation, runtime, external-service, and storage boundaries.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the live architecture inventory and layout contract** - `d94ad4a` (`docs`)
2. **Task 2: Build the editable Excalidraw system diagram from the contract** - `682f1ae` (`docs`)

## Files Created/Modified

- `docs/architecture/system-diagram-contract.md` - source-of-truth component inventory, scope boundary, and required edge list
- `docs/architecture/system-diagram.excalidraw` - editable architecture diagram source used for the README export

## Decisions Made

- Keep the current-state architecture view anchored to `broker_prestaged` even though later execution seams exist elsewhere in the repo.
- Make the proof paths visible inside the diagram so readers can move directly from architecture to verification commands.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Excalidraw retained orphaned arrow-label text nodes after iterative edits, so the clean fix was to rebuild the canvas once without arrow labels before exporting the final source file.

## User Setup Required

None - no external configuration required for this plan.

## Next Phase Readiness

- The README-facing export can now derive from the checked-in Excalidraw source instead of a hand-maintained image.
- Phase 12-02 can focus on the PNG export, README integration, and docs drift guards.

---
*Phase: 12-system-diagram-and-readme-architecture-capture*
*Completed: 2026-04-01*
