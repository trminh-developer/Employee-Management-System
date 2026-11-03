#!/bin/sh
set -e

# ==============================================================================
# TMNexora Docker Entrypoint Script
# ==============================================================================

# Wait for database if DB_WAIT=1
if [ "$DB_WAIT" = "1" ]; then
    echo "[Entrypoint] Waiting for database at ${DB_HOST:-127.0.0.1}:${DB_PORT:-3306}..."
    while ! nc -z "${DB_HOST:-127.0.0.1}" "${DB_PORT:-3306}"; do
        sleep 1
    done
    echo "[Entrypoint] Database is ready!"
fi

# Run database migrations automatically when AUTO_MIGRATE=1
if [ "$AUTO_MIGRATE" = "1" ]; then
    echo "[Entrypoint] Running database migrations..."
    python manage.py migrate --noinput
fi

# Run Gunicorn WSGI server (Django Web UI) or Uvicorn ASGI server (FastAPI REST API)
if [ "$1" = 'gunicorn' ]; then
    echo "[Entrypoint] Starting Gunicorn WSGI production server on port ${PORT:-8000}..."
    exec gunicorn \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers ${GUNICORN_WORKERS:-3} \
        --threads ${GUNICORN_THREADS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-60} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${DJANGO_LOG_LEVEL:-info} \
        config.wsgi:application
elif [ "$1" = 'fastapi' ]; then
    LOG_LEVEL_LOWER=$(echo "${DJANGO_LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
    echo "[Entrypoint] Starting FastAPI Uvicorn ASGI server on port ${PORT:-8001}..."
    exec uvicorn \
        fastapi_main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8001} \
        --workers ${UVICORN_WORKERS:-2} \
        --log-level "$LOG_LEVEL_LOWER"
fi

# Pass-through other commands (e.g. migrate, createsuperuser, shell)
exec "$@"
