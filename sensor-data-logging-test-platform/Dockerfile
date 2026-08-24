# Use a small official Python runtime image.
FROM python:3.12-slim

# Keep Python logs visible and prevent unnecessary bytecode files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies before copying source to improve build caching.
COPY requirements.txt pyproject.toml ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy and install the application as a normal Python package.
COPY src ./src
RUN python -m pip install .

# Run the application as a non-root user.
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && mkdir -p /app/data /app/reports \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000
EXPOSE 8501

# The default container process runs the REST API.
CMD ["uvicorn", "sensor_platform.api:app", "--host", "0.0.0.0", "--port", "8000"]
