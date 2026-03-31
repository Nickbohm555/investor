#!/bin/sh
set -eu

REPO_ROOT="${INVESTOR_REPO_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
LOG_PATH="logs/cron/daily-trigger.log"
BEGIN_MARKER="# >>> investor daily schedule >>>"
END_MARKER="# <<< investor daily schedule <<<"
CRON_LINE="30 8 * * 1-5 cd \"$REPO_ROOT\" && ./scripts/cron-trigger.sh >> ./$LOG_PATH 2>&1"

mkdir -p "$REPO_ROOT/logs/cron"

CURRENT_CONTENT="$(crontab -l 2>/dev/null || true)"
FILTERED_CONTENT="$(printf '%s\n' "$CURRENT_CONTENT" | awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
  $0 == begin { skip=1; next }
  $0 == end { skip=0; next }
  skip != 1 { print }
')"

{
  if [ -n "$FILTERED_CONTENT" ]; then
    printf '%s\n' "$FILTERED_CONTENT"
  fi
  printf '%s\n' "$BEGIN_MARKER"
  printf '%s\n' "$CRON_LINE"
  printf '%s\n' "$END_MARKER"
} | crontab -
