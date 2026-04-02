# Phase 15 Live Proof Runbook

## Reachability

Record the exact public URL used for `INVESTOR_EXTERNAL_BASE_URL` before starting the proof. Note whether the proof depends on a host-port remap, reverse proxy, or tunnel, and record that choice in `15-LIVE-PROOF-RESULT.md`.

The pre-send approval probe target is `<INVESTOR_EXTERNAL_BASE_URL>/approval/probe`. The expected success condition is any app-originated HTTP response from that URL, including `404` or `405`, because those responses prove the public host reaches the approval-path boundary. DNS, TCP connect, TLS, or timeout failures block the proof.

## Preflight

Run:

```bash
python -m app.ops.live_proof preflight
```

Review the JSON output before doing anything else:

- `quiver_checks` must show successful checks for the four live endpoints the repo uses.
- `llm_check` must show the OpenAI-compatible `/chat/completions` tool-call probe.
- `smtp_check` must show the configured SMTP host, port, and STARTTLS behavior.
- `reachability_check` must show a reachable approval boundary.

If the approval-boundary `reachability_check` is not reachable, stop and fix `INVESTOR_EXTERNAL_BASE_URL` before attempting `python -m app.ops.live_proof trigger-scheduled`.

## Start The Runtime

Start the shipped runtime with:

```bash
docker compose up -d --build
docker compose logs -f migrate app
```

Do not proceed until the logs show the app and migration services are healthy.

## Trigger The Live Run

Run:

```bash
python -m app.ops.live_proof trigger-scheduled
```

Only a returned `status` of `started` counts as the passing path. Copy the returned `run_id` into `.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-LIVE-PROOF-RESULT.md` immediately. Any `duplicate`, `failed-preflight`, `blocked`, or other status is a failed or aborted proof and must be recorded as such.

## Inbox Verification

Check the inbox configured by `INVESTOR_DAILY_MEMO_TO_EMAIL`. Confirm that the memo for the recorded `run_id` arrived and record the recipient address in the result file.

## Approval Callback

Inspect the delivered approval link and confirm the host matches `INVESTOR_EXTERNAL_BASE_URL`. Click the live approval link once from the delivered memo and record the observed callback result in the result file.

## Persisted State Verification

Run:

```bash
python -m app.ops.live_proof inspect-run --run-id <run_id>
```

Successful proof requires populated `current_step`, populated `approval_status`, at least one approval event, and recorded state transitions for the same run.

## Observed Logs

Capture the exact observed scheduled-trigger and memo-delivery lines from:

```bash
docker compose logs --no-color app
```

Copy the exact matching lines into the result file so the proof includes both scheduled-trigger and memo-delivery evidence.

## Failure Markers

- `scheduled_trigger result=failure`
- `memo_delivery result=failure`
- Public callback reachability never returns an app-originated HTTP response from `approval/probe`
