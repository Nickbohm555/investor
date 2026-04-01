#!/bin/sh
set -eu

BEGIN_MARKER="# >>> investor daily schedule >>>"
LOG_PATH="${INVESTOR_CRON_LOG_PATH:-logs/cron/daily-trigger.log}"
CRON_EXPRESSION="${INVESTOR_SCHEDULE_CRON_EXPRESSION:-0 7 * * 1-5}"
CRON_TIMEZONE="${INVESTOR_SCHEDULE_TIMEZONE:-America/New_York}"
CURRENT_CONTENT="$(crontab -l 2>/dev/null || true)"

if printf '%s\n' "$CURRENT_CONTENT" | grep -Fq "$BEGIN_MARKER"; then
  printf 'managed=present\n'
else
  printf 'managed=absent\n'
fi
printf 'cron_expression=%s\n' "$CRON_EXPRESSION"
printf 'cron_timezone=%s\n' "$CRON_TIMEZONE"
printf 'log_path=%s\n' "$LOG_PATH"
