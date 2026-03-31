#!/bin/sh
set -eu

PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH

REPO_ROOT="${INVESTOR_REPO_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
cd "$REPO_ROOT"

if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

LOG_PATH="${INVESTOR_CRON_LOG_PATH:-logs/cron/daily-trigger.log}"
CURL_BIN="${INVESTOR_CURL_BIN:-curl}"
mkdir -p "$(dirname "$LOG_PATH")"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

if "$CURL_BIN" -fsS -X POST "$INVESTOR_SCHEDULE_TRIGGER_URL" \
  -H "X-Investor-Scheduled-Trigger: $INVESTOR_SCHEDULED_TRIGGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"replay":false}' >/dev/null; then
  printf '%s scheduled_trigger status=success\n' "$(timestamp)" >> "$LOG_PATH"
else
  printf '%s scheduled_trigger status=failure\n' "$(timestamp)" >> "$LOG_PATH"
  exit 1
fi
