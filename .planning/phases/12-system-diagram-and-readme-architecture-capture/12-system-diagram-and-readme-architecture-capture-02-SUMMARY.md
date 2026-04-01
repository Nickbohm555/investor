---
phase: 12-system-diagram-and-readme-architecture-capture
plan: 02
subsystem: docs
tags: [architecture, readme, png, pytest, docs]
requires:
  - phase: 12-system-diagram-and-readme-architecture-capture
    provides: architecture contract and editable Excalidraw source
provides:
  - README-visible architecture section near the repo entry point
  - exported PNG derived from the Excalidraw source
  - docs drift checks for the architecture section and assets
affects: [readme, docs, operations]
tech-stack:
  added: []
  patterns:
    - readme architecture assets stay pinned by pytest drift coverage
key-files:
  created:
    - docs/architecture/system-diagram.png
  modified:
    - README.md
    - tests/ops/test_operational_docs.py
    - .planning/ROADMAP.md
    - .planning/STATE.md
key-decisions:
  - "The README architecture copy explicitly states that the current approved path ends at broker_prestaged rather than direct order submission."
  - "The PNG export remains a checked-in derivative of the Excalidraw source so the repo stays self-contained on GitHub and local clones."
patterns-established:
  - "Any architecture-doc change must keep README.md, docs/architecture/system-diagram.png, docs/architecture/system-diagram.excalidraw, and tests/ops/test_operational_docs.py aligned."
requirements-completed: [ARCH-03]
duration: 3min
completed: 2026-04-01
---

# Phase 12: System Diagram And README Architecture Capture Summary

**The repo entry point now shows a checked-in architecture image and truthful orientation copy, with tests that fail if the section or assets drift away.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-01T01:28:18Z
- **Completed:** 2026-04-01T01:30:41Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added red-first docs tests for the architecture section and both diagram assets, then drove them green with the README and PNG export.
- Exported the README screenshot directly from the checked-in Excalidraw source.
- Added a concise architecture section near the top of `README.md` that keeps the runtime boundary truthful to `broker_prestaged`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing docs drift checks for the architecture section and diagram assets** - `71bbfbc` (`test`)
2. **Task 2: Export the README screenshot and integrate the truthful architecture section** - `967fa0e` (`docs`)
3. **Task 3: Manually verify README screenshot legibility and truthful runtime scope** - verified inline against the rendered export and README placement

## Files Created/Modified

- `docs/architecture/system-diagram.png` - checked-in PNG export derived from the Excalidraw source
- `README.md` - top-level architecture section with image embed and truthful runtime boundary copy
- `tests/ops/test_operational_docs.py` - red/green docs drift coverage for the architecture section and assets
- `.planning/ROADMAP.md` - Phase 12 completion tracking
- `.planning/STATE.md` - phase completion and new architecture decision tracking

## Decisions Made

- Treat the screenshot legibility checkpoint as satisfied only after the export rendered clearly enough at README scale and stayed visible near the top of the file.
- Keep the README architecture prose short and operator-facing rather than duplicating the full contract in prose.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external configuration required for this plan.

## Next Phase Readiness

- Phase 12 now exposes the architecture at the repo entry point and keeps the source/export/test set aligned.
- The next workflow step can verify or close the milestone without additional architecture documentation work.

---
*Phase: 12-system-diagram-and-readme-architecture-capture*
*Completed: 2026-04-01*
