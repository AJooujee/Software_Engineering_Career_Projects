FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first to preserve Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Inventory API and database migrations.
COPY app ./app
COPY alembic.ini .
COPY migrations ./migrations

# Run the service without root privileges.
RUN groupadd --system app \
    && useradd --system --gid app app \
    && chown -R app:app /app

USER app

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]