#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 \"<test instructions>\"" >&2
  echo "How to run: ./superpower.sh \"test the investor workflow end to end and fix failures\"" >&2
  exit 1
fi

TEST_INSTRUCTIONS="$*"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_SUFFIX="make sure this works, track the data flow, find the root cause if there are errors and solve them"
COMMIT_PUSH_INSTRUCTION="If you make code changes, create an atomic git commit for your changes and push them before finishing. If you do not make code changes, do not create an empty commit."

if [ "${SUPERPOWER_CAFFEINATED:-0}" != "1" ]; then
  exec env SUPERPOWER_CAFFEINATED=1 caffeinate -dimu "$0" "$@"
fi

codex exec \
  --cd "$REPO_ROOT" \
  --dangerously-bypass-approvals-and-sandbox \
  - <<EOF
Start a fresh Codex session and do \$writing-plans.
Do not ask clarifying questions, ask for approval, or ask me to choose an execution approach.
If there are design decisions to make, make them.
There should be exactly one superpowers spec for this work in docs/superpowers/specs.
Use that single spec instead of creating multiple superpowers specs.
After the plan is written and committed, stop.
$COMMIT_PUSH_INSTRUCTION
EOF

codex exec \
  --cd "$REPO_ROOT" \
  --dangerously-bypass-approvals-and-sandbox \
  - <<EOF
Start a fresh Codex session and do \$executing-plans.
Make reasonable assumptions and continue without waiting for user input.
There should be exactly one superpowers plan for this work in docs/superpowers/plans.
Use that single plan instead of creating or selecting multiple superpowers plans.
Do not present branch-management options or ask me what to do next.
If the skill would normally offer choices at the end, choose the path that finishes the work, pushes any new commits, and exits.
$COMMIT_PUSH_INSTRUCTION
EOF

codex exec \
  --cd "$REPO_ROOT" \
  --dangerously-bypass-approvals-and-sandbox \
  - <<EOF
Start a fresh final Codex session for cleanup after the planning, execution, and testing sessions.
Make reasonable assumptions and continue without waiting for user input.
Review the end-to-end flow for this requested work and identify code that is now obsolete, dead, or unused.
Use \$code-simplifier to simplify or remove that obsolete code without changing behavior.
Use git diff, git log, and the current runtime paths to verify what changed and what is still needed.
Do not broaden scope beyond cleanup that is justified by the current request.
Do not ask for approval before making justified cleanup changes.
$COMMIT_PUSH_INSTRUCTION
EOF
