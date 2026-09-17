# syntax=docker/dockerfile:1

# Build dependencies inside an isolated virtual environment. Keeping build
# tooling out of the final image reduces image size and production attack area.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /build

# Create a portable virtual environment that can be copied into the runtime
# stage without reinstalling packages there.
RUN python -m venv /opt/venv

# Copy package metadata and source before installing the application.
COPY pyproject.toml README.md ./
COPY src ./src

# Install only runtime dependencies. Development tools remain outside the
# production image.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .


# Use a fresh runtime stage so build caches and temporary files are discarded.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOME="/home/observability"

WORKDIR /app

# A fixed numeric identity makes runtime ownership predictable across hosts.
RUN groupadd --gid 10001 observability \
    && useradd \
        --uid 10001 \
        --gid 10001 \
        --create-home \
        --home-dir /home/observability \
        --shell /usr/sbin/nologin \
        observability

# Copy the ready-to-run environment and application migration files.
COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 alembic.ini ./
COPY --chown=10001:10001 migrations ./migrations

# Run the API without root privileges.
USER 10001:10001

EXPOSE 8000

# Liveness does not depend on PostgreSQL, so Docker can distinguish a failed
# process from a temporarily unavailable external dependency.
HEALTHCHECK \
    --interval=10s \
    --timeout=3s \
    --start-period=10s \
    --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)" || exit 1

# Use exec form so Uvicorn receives container termination signals directly.
# Use exec form so Uvicorn receives container termination signals directly.
CMD ["uvicorn", "observability_platform.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
