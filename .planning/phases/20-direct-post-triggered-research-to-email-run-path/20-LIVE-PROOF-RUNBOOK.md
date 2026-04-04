# Phase 20 Direct POST Delivery Proof Runbook

## Preflight

Run:

```bash
python -m app.ops.live_proof preflight
```

Record `first_blocking_failure`, `blocking_failures`, `warnings`, `smtp_ready`, and `approval_reachability_ready` in `20-LIVE-PROOF-RESULT.md` before starting the runtime. If `blocking_failures` is non-empty, stop and record the first exact readiness string instead of attempting the direct run.

## Start The Runtime

Start the shipped runtime with:

```bash
docker compose up -d --build
docker compose logs -f migrate app
```

Do not proceed until the app is healthy enough to accept `POST /runs/trigger`.

## Trigger The Direct Run

Run:

```bash
python -m app.ops.live_proof trigger-manual
```

This command posts directly to `POST /runs/trigger` with no scheduled headers. Only `manual_trigger_status_code: 202` with `manual_trigger_ok: true` counts as a passing trigger result. Copy the returned `run_id` into `20-LIVE-PROOF-RESULT.md` immediately.

## Inbox Verification

Check the inbox configured by `INVESTOR_DAILY_MEMO_TO_EMAIL`. The Phase 20 proof target is delivered email, not approval-link execution. Record the verified recipient in the result file and confirm the memo corresponds to the recorded manual run id.

## Approval Host Verification

Inspect the delivered memo and record the rendered approval link host. The host must truthfully reflect `INVESTOR_EXTERNAL_BASE_URL`, but approval-link clicking is not required for Phase 20.

## Persisted State Verification

Run:

```bash
python -m app.ops.live_proof inspect-run --run-id <run_id>
```

Record `current_step`, `approval_status`, and `final_run_status`. Successful Phase 20 proof should show the persisted run at `awaiting_review` after the memo is sent.

## Observed Logs

Capture the exact observed `manual_trigger result=` and `memo_delivery result=` lines from:

```bash
docker compose logs --no-color app
```

Copy the exact matching lines into the result file when present.

## Failure Markers

- `blocking_failures` is non-empty
- `manual_trigger_status_code` is not `202`
- `manual_trigger_ok` is not `true`
- `manual_trigger result=failure`
- `memo_delivery result=failure`
- The memo never reaches `INVESTOR_DAILY_MEMO_TO_EMAIL`
- The delivered approval link host does not match `INVESTOR_EXTERNAL_BASE_URL`

