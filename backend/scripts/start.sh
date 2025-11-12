#!/bin/bash
set -euo pipefail

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
  log "ERROR: $1"
  exit 1
}

LOG_DIR="${DJANGO_SCHEDULER_LOG_DIR:-/app/logs}"
mkdir -p "${LOG_DIR}"
chown django:django "${LOG_DIR}"
touch "${LOG_DIR}/access.log" "${LOG_DIR}/error.log"
chown django:django "${LOG_DIR}/access.log" "${LOG_DIR}/error.log"

log "Checking database connectivity..."
for attempt in {1..60}; do
  if gosu django python manage.py check --database default >/dev/null 2>&1; then
    log "Database connection established."
    break
  fi
  if [[ "${attempt}" -eq 60 ]]; then
    log "Database connection failed after ${attempt} attempts."
    log "DB_HOST=${DB_HOST:-unset}"
    log "DB_PORT=${DB_PORT:-unset}"
    log "DB_USER=${DB_USER:-unset}"
    log "DB_NAME=${DB_NAME:-unset}"
    error_exit "Database connection failed."
  fi
  log "Waiting for database... (attempt ${attempt}/60)"
  sleep 1
done

log "Running migrations..."
gosu django python manage.py makemigrations || error_exit "makemigrations failed."
gosu django python manage.py migrate --noinput || error_exit "migrate failed."
log "Migrations completed successfully."

log "Starting scheduler..."
gosu django python /app/scheduler.py &
SCHEDULER_PID=$!

cleanup() {
  local exit_code=$?
  if kill -0 "${SCHEDULER_PID}" 2>/dev/null; then
    log "Stopping scheduler (PID: ${SCHEDULER_PID})"
    kill "${SCHEDULER_PID}" 2>/dev/null || true
    wait "${SCHEDULER_PID}" 2>/dev/null || true
  fi
  if [[ -n "${GUNICORN_PID:-}" ]] && kill -0 "${GUNICORN_PID}" 2>/dev/null; then
    log "Stopping Gunicorn (PID: ${GUNICORN_PID})"
    kill "${GUNICORN_PID}" 2>/dev/null || true
    wait "${GUNICORN_PID}" 2>/dev/null || true
  fi
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

WORKERS=$(( $(nproc) * 2 + 1 ))

log "Starting Gunicorn with ${WORKERS} workers..."
gosu django gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${WORKERS}" \
  --worker-class sync \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --keep-alive 2 \
  --access-logfile "${LOG_DIR}/access.log" \
  --error-logfile "${LOG_DIR}/error.log" \
  --log-level info \
  --preload \
  --capture-output \
  --enable-stdio-inheritance &
GUNICORN_PID=$!

wait "${GUNICORN_PID}"
