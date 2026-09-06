# syntax=docker/dockerfile:1

# Build Python dependencies separately so the runtime image stays focused.
FROM python:3.12-slim AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace/backend

COPY requirements.txt ./

RUN pip install --requirement requirements.txt


# Run the API as a dedicated non-root user.
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/workspace/backend" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd \
        --system \
        --gid 10001 \
        cloudops \
    && useradd \
        --system \
        --uid 10001 \
        --gid cloudops \
        --no-create-home \
        --home-dir /nonexistent \
        --shell /usr/sbin/nologin \
        cloudops

WORKDIR /workspace/backend

COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=cloudops:cloudops alembic.ini ./
COPY --chown=cloudops:cloudops migrations ./migrations
COPY --chown=cloudops:cloudops app ./app

RUN python -m compileall -q app

USER 10001:10001

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
