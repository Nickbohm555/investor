#!/bin/sh
set -eu

if [ -z "${INVESTOR_SCHEDULED_TRIGGER_TOKEN:-}" ]; then
  echo "INVESTOR_SCHEDULED_TRIGGER_TOKEN must be set" >&2
  exit 1
fi

envsubst < /app/ops/scheduler/crontab > /tmp/investor.crontab
cat /tmp/investor.crontab

exec /usr/local/bin/supercronic /tmp/investor.crontab
