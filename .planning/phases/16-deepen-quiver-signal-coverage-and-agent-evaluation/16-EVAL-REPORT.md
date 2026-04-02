# Phase 16 Evaluation Report

Generated on `2026-04-02` from the repo-owned Phase 16 evaluation harness.

## Comparison

- Baseline label: `baseline`
- Tuned label: `tuned`
- Baseline total score: `2.25`
- Tuned total score: `3.00`
- Total delta: `+0.75`

## Case Deltas

| Case | Baseline | Tuned | Delta | Why it improved |
|------|----------|-------|-------|-----------------|
| `candidate-high-conviction` | `0.85` | `1.00` | `+0.15` | Tuned output preserved explicit trace rationale. |
| `watchlist-mixed-signals` | `0.70` | `1.00` | `+0.30` | Tuned output added complete watchlist guidance plus trace rationale. |
| `no-action-stale-evidence` | `0.70` | `1.00` | `+0.30` | Tuned output added explicit no-action reasons plus trace rationale. |

## Interpretation

- The measured gain came from two quality seams Phase 16 targeted directly:
  - richer follow-up rationale in traces
  - explicit stale/conflicting/missing-confirmation framing in non-candidate outputs
- The shortlist and evidence-summary changes are now in place to support those better outputs with fresher context.
- No budget increase was required to realize the measured gain, so the default budget stays unchanged in this phase.

## Commands

Primary verification command:

```bash
python -m pytest tests/services/test_quiver_normalize.py tests/agents/test_quiver_loop.py tests/services/test_research_prompt.py tests/evals/test_harness.py -q
```
