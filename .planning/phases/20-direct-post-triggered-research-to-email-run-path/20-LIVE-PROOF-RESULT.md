manual_trigger_status_code: not-started
manual_trigger_ok: not-started
manual_trigger_run_id: not-started
first_blocking_failure: not-evaluated
blocking_failures: none-recorded
warnings: none-recorded
memo_delivered_to: not-verified
approval_link_host: not-observed
current_step: not-started
approval_status: not-started
final_run_status: not-started
remaining_manual_steps: run `python -m app.ops.live_proof preflight`, start the runtime with `docker compose up -d --build`, run `python -m app.ops.live_proof trigger-manual`, inspect the inbox for the delivered memo, run `python -m app.ops.live_proof inspect-run --run-id <run_id>`, and capture the exact manual_trigger and memo_delivery log lines
