# Observability & Incident Detection Platform

A backend platform for collecting operational telemetry, monitoring service
health, detecting abnormal behavior, and managing incidents.

The project is being developed incrementally to demonstrate backend engineering,
observability, automated testing, and production-oriented system design.

## Current Status

Phase 1: Foundation and Service Bootstrap

Implemented:

- FastAPI application foundation
- Health-check endpoint
- Environment-based configuration
- Request ID middleware
- Structured JSON request logging
- Automated API and middleware tests
- Ruff linting and formatting

## Technology Stack

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic Settings
- Pytest
- HTTPX2
- Ruff

## Project Structure

```text
observability-incident-detection-platform/
├── .github/
│   └── workflows/
├── docs/
├── src/
│   └── observability_platform/
│       ├── __init__.py
│       ├── config.py
│       ├── logging_config.py
│       ├── main.py
│       └── middleware.py
├── tests/
│   ├── test_health.py
│   └── test_middleware.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Local Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the application and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the Application

```powershell
python -m uvicorn observability_platform.main:app --reload
```

Available endpoints:

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Configuration

Configuration can be supplied using environment variables with the
`OBSERVABILITY_` prefix.

Example:

```powershell
$env:OBSERVABILITY_ENVIRONMENT = "production"
$env:OBSERVABILITY_LOG_LEVEL = "WARNING"
```

Supported environments:

- `development`
- `testing`
- `production`

## Quality Checks

Run automated tests:

```powershell
python -m pytest -v
```

Run linting:

```powershell
python -m ruff check .
```

Check formatting:

```powershell
python -m ruff format --check .
```

## Development Roadmap

1. Foundation and service bootstrap
2. Telemetry ingestion API
3. Persistent telemetry storage and service registry
4. Rule-based anomaly and incident detection
5. Alerting and incident lifecycle management
6. Event correlation and root-cause analysis
7. Metrics dashboards and distributed tracing
8. Containerization, CI/CD, security, and production hardening