#!/bin/sh
set -eu

BEGIN_MARKER="# >>> investor daily schedule >>>"
LOG_PATH="logs/cron/daily-trigger.log"
CURRENT_CONTENT="$(crontab -l 2>/dev/null || true)"

if printf '%s\n' "$CURRENT_CONTENT" | grep -Fq "$BEGIN_MARKER"; then
  printf 'managed=present\n'
else
  printf 'managed=absent\n'
fi
printf 'log_path=%s\n' "$LOG_PATH"
