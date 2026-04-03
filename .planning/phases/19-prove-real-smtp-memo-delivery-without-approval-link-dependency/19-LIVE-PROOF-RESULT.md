run_id: not-started
scheduled_trigger_status: blocked-before-trigger (scheduled route never invoked; preflight exited with httpx.ConnectError: [Errno 8] nodename nor servname provided, or not known)
memo_delivered_to: not-attempted (no inbox verification possible because the run never started)
approval_link_host: not-observed (no delivered memo to inspect)
approval_callback_status: skipped-for-phase-19
smtp_ready: not-evaluated (preflight aborted before SMTP inspection)
approval_reachability_ready: not-evaluated (preflight aborted before approval probe)
blocking_failures: preflight-aborted-before-smtp (Quiver live endpoint lookup failed with httpx.ConnectError: [Errno 8] nodename nor servname provided, or not known)
warnings: none-recorded (preflight aborted before warning classification)
scheduled_trigger_log_line: not-observed (scheduled_trigger result= unavailable because `docker compose up -d --build` failed with Cannot connect to the Docker daemon at unix:///Users/nickbohm/.docker/run/docker.sock. Is the docker daemon running?)
memo_delivery_log_line: not-observed (memo_delivery result= unavailable because no run reached the SMTP delivery step)
current_step: not-started
approval_status: not-started
final_run_status: blocked-before-trigger (Quiver preflight failed with httpx.ConnectError: [Errno 8] nodename nor servname provided, or not known; Docker daemon unavailable for `docker compose up -d --build`)
remaining_manual_steps: start the Docker daemon; set a reachable `INVESTOR_QUIVER_BASE_URL`; ensure live SMTP host/port and any required `INVESTOR_SMTP_SECURITY` value are configured; set `INVESTOR_OPENAI_BASE_URL`, `INVESTOR_OPENAI_MODEL`, and `INVESTOR_EXTERNAL_BASE_URL`; rerun `python -m app.ops.live_proof preflight`, `docker compose up -d --build`, `python -m app.ops.live_proof trigger-scheduled`, `python -m app.ops.live_proof inspect-run --run-id <run_id>`, and the manual inbox/approval-host verification steps from the Phase 19 runbook
