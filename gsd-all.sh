#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  gsd-all plan N [--repo PATH] [--no-push]
  gsd-all plan START:END [--repo PATH] [--no-push]
  gsd-all plan 1,3,4 [--repo PATH] [--no-push]
  gsd-all execute N [--repo PATH] [--no-push]
  gsd-all execute START:END [--repo PATH] [--no-push]
  gsd-all execute 1,3,4 [--repo PATH] [--no-push]

Options:
  --repo PATH     Repo root (default: current working directory)
  --no-push       Skip pushing to origin after plan/execute work
USAGE
}

repo="$(pwd)"
mode="${1:-}"
phase_arg="${2:-}"
push_enabled=true

push_current_branch() {
  local branch
  branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"

  if [[ -z "$branch" || "$branch" == "HEAD" ]]; then
    echo "Cannot push: repo is in detached HEAD state." >&2
    return 1
  fi

  if ! git -C "$repo" remote get-url origin >/dev/null 2>&1; then
    echo "Cannot push: remote 'origin' is not configured for $repo." >&2
    return 1
  fi

  git -C "$repo" push -u origin "$branch"
}

if [[ -z "$mode" || -z "$phase_arg" ]]; then
  usage
  exit 1
fi

shift 2

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="$2"
      shift 2
      ;;
    --no-push)
      push_enabled=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$phase_arg" =~ ^[0-9]+$ ]]; then
  phases=()
  for ((i=1; i<=phase_arg; i++)); do
    phases+=("$i")
  done
elif [[ "$phase_arg" =~ ^([0-9]+):([0-9]+)$ ]]; then
  start="${BASH_REMATCH[1]}"
  end="${BASH_REMATCH[2]}"

  if (( start > end )); then
    echo "Invalid phase range: $phase_arg (start must be <= end)" >&2
    exit 1
  fi

  phases=()
  for ((i=start; i<=end; i++)); do
    phases+=("$i")
  done
else
  IFS=',' read -r -a phases <<<"$phase_arg"
fi

if [[ "$mode" == "plan" ]]; then
  for phase in "${phases[@]}"; do
    codex exec --dangerously-bypass-approvals-and-sandbox -C "$repo" - <<EOF &
Use \$gsd-plan-phase $(echo "$phase" | xargs)
EOF
  done
  wait

  if [[ "$push_enabled" == true ]]; then
    echo "Pushing branch after planning..."
    push_current_branch || {
      echo "Push failed after planning. Resolve and rerun." >&2
      exit 1
    }
  fi
fi

for phase in "${phases[@]}"; do
  codex exec --dangerously-bypass-approvals-and-sandbox -C "$repo" - <<EOF
Use \$gsd-execute-phase $(echo "$phase" | xargs)
EOF

  if [[ "$push_enabled" == true ]]; then
    echo "Pushing branch after execute phase $(echo "$phase" | xargs)..."
    push_current_branch || {
      echo "Push failed after execute phase $(echo "$phase" | xargs). Resolve and rerun." >&2
      exit 1
    }
  fi
done
