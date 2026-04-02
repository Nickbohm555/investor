# Quiver Research Flow Contract

This file is the source-of-truth inventory for the editable Quiver research-flow diagram in `docs/architecture/quiver-research-flow.excalidraw`.

## Endpoints

- `/beta/live/congresstrading`
- `/beta/live/insiders`
- `/beta/live/govcontracts`
- `/beta/live/lobbying`

## Purpose

- `/beta/live/congresstrading` -> `broad unusual legislative trade signal`
- `/beta/live/insiders` -> `ticker-specific corporate insider confirmation`
- `/beta/live/govcontracts` -> `contract-backed demand / revenue context`
- `/beta/live/lobbying` -> `policy/regulatory interest context`

## Flow

`QuiverClient live calls -> build_ticker_evidence_bundles -> shortlist seeds -> follow-up investigation -> finalize_research_outcome -> final recommendations`

## README Copy

The README section must be named `## Quiver Research Flow`, embed `docs/architecture/quiver-research-flow.png`, and explain that `/beta/live/congresstrading` adds the broad unusual legislative trade signal, `/beta/live/insiders` adds ticker-specific corporate insider confirmation, `/beta/live/govcontracts` adds contract-backed demand / revenue context, and `/beta/live/lobbying` adds policy/regulatory interest context before the research loop turns that evidence into shortlist seeds, follow-up investigation, and final recommendations.
