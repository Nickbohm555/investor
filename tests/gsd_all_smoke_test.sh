#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
OUT_DIR="$TMP_DIR/out"
mkdir -p "$BIN_DIR" "$OUT_DIR"

cat > "$BIN_DIR/caffeinate" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

while [[ $# -gt 0 ]]; do
  case "$1" in
    -*)
      shift
      ;;
    *)
      break
      ;;
  esac
done

exec "$@"
EOF

cat > "$BIN_DIR/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

lock_dir="${GSD_ALL_TEST_LOCK_DIR:?}"
log_file="${GSD_ALL_TEST_LOG_FILE:?}"

if ! mkdir "$lock_dir" 2>/dev/null; then
  echo "concurrent codex invocation detected" >&2
  exit 91
fi

cleanup() {
  rmdir "$lock_dir"
}
trap cleanup EXIT

prompt="$(cat)"
printf '%s\n' "$prompt" | sed -n '1p' >> "$log_file"
sleep 0.2
EOF

chmod +x "$BIN_DIR/caffeinate" "$BIN_DIR/codex"

GSD_ALL_TEST_LOCK_DIR="$OUT_DIR/codex.lock" \
GSD_ALL_TEST_LOG_FILE="$OUT_DIR/prompts.log" \
PATH="$BIN_DIR:$PATH" \
"$REPO_ROOT/gsd-all.sh" plan 3 --repo "$REPO_ROOT" --no-push

expected=$'Use $gsd-plan-phase 1\nUse $gsd-plan-phase 2\nUse $gsd-plan-phase 3'
actual="$(sed -n '1,3p' "$OUT_DIR/prompts.log")"

if [[ "$actual" != "$expected" ]]; then
  echo "Unexpected prompt order" >&2
  echo "Expected:" >&2
  printf '%s\n' "$expected" >&2
  echo "Actual:" >&2
  printf '%s\n' "$actual" >&2
  exit 1
fi

echo "gsd-all.sh smoke test passed"
