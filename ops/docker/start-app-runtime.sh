#!/bin/sh
set -eu

SUPERCRONIC_PID=""
UVICORN_PID=""

stop_children() {
  if [ -n "${SUPERCRONIC_PID}" ] && kill -0 "${SUPERCRONIC_PID}" 2>/dev/null; then
    kill "${SUPERCRONIC_PID}" 2>/dev/null || true
  fi
  if [ -n "${UVICORN_PID}" ] && kill -0 "${UVICORN_PID}" 2>/dev/null; then
    kill "${UVICORN_PID}" 2>/dev/null || true
  fi
}

trap 'stop_children' INT TERM

/app/ops/scheduler/start-supercronic.sh &
SUPERCRONIC_PID=$!

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

wait "${UVICORN_PID}"
STATUS=$?
stop_children
wait "${SUPERCRONIC_PID}" || true
exit "${STATUS}"
