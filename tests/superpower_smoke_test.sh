#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
OUT_DIR="$TMP_DIR/out"
mkdir -p "$BIN_DIR" "$OUT_DIR"

cat > "$BIN_DIR/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

count_file="${SUPERPOWER_TEST_COUNT_FILE:?}"
out_dir="${SUPERPOWER_TEST_OUT_DIR:?}"
count=0
if [ -f "$count_file" ]; then
  count="$(cat "$count_file")"
fi
count="$((count + 1))"
printf '%s' "$count" > "$count_file"
cat > "$out_dir/prompt-$count.txt"
EOF

chmod +x "$BIN_DIR/codex"

SUPERPOWER_CAFFEINATED=1 \
SUPERPOWER_TEST_COUNT_FILE="$OUT_DIR/count" \
SUPERPOWER_TEST_OUT_DIR="$OUT_DIR" \
PATH="$BIN_DIR:$PATH" \
"$REPO_ROOT/superpower.sh" "dummy instructions"

assert_contains() {
  local file="$1"
  local expected="$2"

  if ! grep -Fq "$expected" "$file"; then
    echo "Expected to find: $expected" >&2
    echo "In file: $file" >&2
    echo "--- file contents ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

assert_contains "$OUT_DIR/prompt-1.txt" "Do not ask clarifying questions, ask for approval, or ask me to choose an execution approach."
assert_contains "$OUT_DIR/prompt-1.txt" "After the plan is written and committed, stop."

assert_contains "$OUT_DIR/prompt-2.txt" "Make reasonable assumptions and continue without waiting for user input."
assert_contains "$OUT_DIR/prompt-2.txt" "Do not present branch-management options or ask me what to do next."

assert_contains "$OUT_DIR/prompt-3.txt" "Make reasonable assumptions and continue without waiting for user input."
assert_contains "$OUT_DIR/prompt-3.txt" "Do not ask for approval before making justified cleanup changes."

echo "superpower.sh smoke test passed"
