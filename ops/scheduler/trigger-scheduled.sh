#!/bin/sh
set -eu

RESPONSE_FILE="$(mktemp)"
HTTP_CODE="$(
  curl -sS -o "${RESPONSE_FILE}" -w "%{http_code}" \
    -X POST "${INVESTOR_SCHEDULE_TRIGGER_URL:-http://127.0.0.1:8000/runs/trigger/scheduled}" \
    -H "X-Investor-Scheduled-Trigger: ${INVESTOR_SCHEDULED_TRIGGER_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"replay":false}'
)"
RESPONSE="$(cat "${RESPONSE_FILE}")"
rm -f "${RESPONSE_FILE}"

case "${HTTP_CODE}:${RESPONSE}" in
  202:*\"status\":\"started\"*)
    echo "scheduled_trigger result=started"
    ;;
  200:*\"status\":\"duplicate\"*)
    echo "scheduled_trigger result=duplicate"
    ;;
  *)
    echo "scheduled_trigger result=failure"
    exit 1
    ;;
esac
