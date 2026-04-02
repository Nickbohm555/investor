run_id: not-started
scheduled_trigger_status: blocked-before-trigger (docker compose app bind failed on 0.0.0.0:8000; no live INVESTOR_* credentials loaded)
approval_probe_url: https://investor.example.com/approval/probe
approval_probe_status_code: not-reached (preflight stopped earlier on Quiver placeholder host lookup failure)
memo_delivered_to: not-attempted
approval_link_host: not-attempted
approval_callback_status: not-attempted
current_step: not-started
approval_status: not-started
scheduled_trigger_log_line: not-observed (scheduled trigger never ran)
memo_delivery_log_line: not-observed (memo delivery never ran)
final_run_status: blocked-before-trigger
approval_event_count: 0
state_transition_count: 0
broker_artifact_count: 0
remaining_manual_steps: provide real INVESTOR_QUIVER_API_KEY, INVESTOR_OPENAI_API_KEY/base URL/model, SMTP settings, INVESTOR_DAILY_MEMO_TO_EMAIL, and INVESTOR_EXTERNAL_BASE_URL; free or remap host port 8000 from web-agent-backend-1; rerun docker compose up -d --build, python -m app.ops.live_proof preflight, python -m app.ops.live_proof trigger-scheduled, inbox approval, inspect-run, and docker compose logs --no-color app
