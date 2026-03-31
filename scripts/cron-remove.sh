#!/bin/sh
set -eu

BEGIN_MARKER="# >>> investor daily schedule >>>"
END_MARKER="# <<< investor daily schedule <<<"
CURRENT_CONTENT="$(crontab -l 2>/dev/null || true)"
FILTERED_CONTENT="$(printf '%s\n' "$CURRENT_CONTENT" | awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
  $0 == begin { skip=1; next }
  $0 == end { skip=0; next }
  skip != 1 { print }
')"

if [ -n "$FILTERED_CONTENT" ]; then
  printf '%s\n' "$FILTERED_CONTENT" | crontab -
else
  crontab -r 2>/dev/null || true
fi
