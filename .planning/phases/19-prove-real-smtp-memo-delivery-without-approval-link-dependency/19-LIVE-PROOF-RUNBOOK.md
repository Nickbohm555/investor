# Phase 19 SMTP Proof Runbook

## Preflight

Run:

```bash
python -m app.ops.live_proof preflight
```

Record `smtp_ready`, `approval_reachability_ready`, `blocking_failures`, and `warnings` in `19-LIVE-PROOF-RESULT.md` before moving on. The expected Phase 19 contract is that approval reachability is a warning for Phase 19, not a blocker. If `blocking_failures` is non-empty, stop and record the exact blocker.

## Start The Runtime

Start the shipped runtime with:

```bash
docker compose up -d --build
docker compose logs -f migrate app
```

Do not proceed until the runtime is healthy enough to accept the scheduled trigger.

## Trigger The Live Run

Run:

```bash
python -m app.ops.live_proof trigger-scheduled
```

Only `status: started` counts as the passing trigger result. Copy the returned `run_id` into `19-LIVE-PROOF-RESULT.md` immediately. Any other status must be recorded as a failed or blocked proof attempt.

## Inbox Verification

Check the inbox configured by `INVESTOR_DAILY_MEMO_TO_EMAIL`. Confirm whether the memo for the recorded `run_id` arrived and record the verified recipient address in the result file.

## Approval Host Verification

Inspect the delivered memo and confirm that the rendered approval link host matches `INVESTOR_EXTERNAL_BASE_URL`. Record the observed host value in `19-LIVE-PROOF-RESULT.md` and record `approval_callback_status: skipped-for-phase-19` instead of clicking the link.

## Persisted State Verification

Run:

```bash
python -m app.ops.live_proof inspect-run --run-id <run_id>
```

Record `current_step` and `approval_status` even when no callback occurred. The proof should show the run's persisted state without requiring callback execution.

## Observed Logs

Capture the exact observed `scheduled_trigger result=` and `memo_delivery result=` lines from:

```bash
docker compose logs --no-color app
```

Copy those exact lines into the result file when present.

## Failure Markers

- `blocking_failures` is non-empty
- `scheduled_trigger result=failure`
- `memo_delivery result=failure`
- The memo never reaches `INVESTOR_DAILY_MEMO_TO_EMAIL`
- The delivered approval link host does not match `INVESTOR_EXTERNAL_BASE_URL`
