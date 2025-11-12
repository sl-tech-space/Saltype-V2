#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

LOG_DIR="${DJANGO_SCHEDULER_LOG_DIR:-/app/logs}"
mkdir -p "${LOG_DIR}"
touch "${LOG_DIR}/access.log" "${LOG_DIR}/error.log"

log "Checking for model changes..."
python manage.py makemigrations --noinput || true

log "Running migrations..."
python manage.py migrate --noinput
log "Migrations completed."

log "Starting scheduler..."
python /app/scheduler.py &
SCHEDULER_PID=$!

cleanup() {
  local exit_code=$?
  if [[ -n "${GUNICORN_PID:-}" ]] && kill -0 "${GUNICORN_PID}" 2>/dev/null; then
    log "Stopping Gunicorn (PID: ${GUNICORN_PID})"
    kill "${GUNICORN_PID}" 2>/dev/null || true
    wait "${GUNICORN_PID}" 2>/dev/null || true
  fi
  if [[ -n "${SCHEDULER_PID:-}" ]] && kill -0 "${SCHEDULER_PID}" 2>/dev/null; then
    log "Stopping scheduler (PID: ${SCHEDULER_PID})"
    kill "${SCHEDULER_PID}" 2>/dev/null || true
    wait "${SCHEDULER_PID}" 2>/dev/null || true
  fi
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

WORKERS=${GUNICORN_WORKERS:-1}
PORT=${BACKEND_PORT:-8000}

log "Starting Gunicorn (reload mode) on ${PORT} with ${WORKERS} worker(s)..."
gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WORKERS}" \
  --reload \
  --access-logfile "${LOG_DIR}/access.log" \
  --error-logfile "${LOG_DIR}/error.log" \
  --log-level debug \
  --capture-output \
  --enable-stdio-inheritance &
GUNICORN_PID=$!

wait "${GUNICORN_PID}"

