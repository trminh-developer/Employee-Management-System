# ------------------------------------------------------------------------------
# Stage 1: Build Dependencies
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ------------------------------------------------------------------------------
# Stage 2: Runtime Production Image
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    GUNICORN_WORKERS=3 \
    GUNICORN_TIMEOUT=60

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -g 10001 tmnexora && \
    useradd -u 10001 -g tmnexora -s /bin/sh -m tmnexora

# Copy Python virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY --chown=tmnexora:tmnexora . /app

# Normalize line endings (CRLF -> LF for Windows hosts) and set executable bit on entrypoint
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Collect static files into STATIC_ROOT during build (using inline env vars so they do not leak into runtime)
RUN DJANGO_SECRET_KEY="build-time-secret-for-static-collection" \
    DJANGO_DEBUG="False" \
    DB_ENGINE="django.db.backends.sqlite3" \
    DB_NAME="build.sqlite3" \
    python manage.py collectstatic --noinput && \
    rm -f /app/build.sqlite3

# Ensure /app, media, and staticfiles directories have non-root ownership
RUN mkdir -p /app/media /app/staticfiles && \
    chown -R tmnexora:tmnexora /app /app/media /app/staticfiles

# Switch to non-root user
USER tmnexora

# Expose internal container ports (8000: Django Web UI, 8001: FastAPI REST Server)
EXPOSE 8000 8001

# Healthcheck probe for standalone Docker runtime (adapts automatically to PORT=8000 or PORT=8001)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/healthz/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn"]
