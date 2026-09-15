# Observability & Incident Detection Platform

A backend platform for collecting operational telemetry, monitoring service
health, detecting abnormal behavior, and managing incidents.

The project is being developed incrementally to demonstrate backend engineering,
observability, automated testing, and production-oriented system design.

## Current Status

Phase 2: Telemetry Ingestion API

Implemented:

- FastAPI application foundation
- Health-check endpoint
- Environment-based configuration
- Request ID middleware
- Structured JSON request logging
- Metric, log, and event telemetry schemas
- Discriminated Pydantic validation
- Batch telemetry ingestion endpoint
- Concurrency-safe in-memory telemetry storage
- Automated unit and API integration tests
- Ruff linting and formatting
- GitHub Actions continuous integration

See [Telemetry Ingestion](docs/telemetry-ingestion.md) for the Phase 2 API
design and validation rules.

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
- Telemetry ingestion: `POST http://127.0.0.1:8000/api/v1/telemetry`
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

- [x] Phase 1: Foundation and service bootstrap
- [x] Phase 2: Telemetry ingestion API
- [ ] Phase 3: Persistent telemetry storage and service registry
- [ ] Phase 4: Rule-based anomaly and incident detection
- [ ] Phase 5: Alerting and incident lifecycle management
- [ ] Phase 6: Event correlation and root-cause analysis
- [ ] Phase 7: Metrics dashboards and distributed tracing
- [ ] Phase 8: Containerization, CI/CD, security, and production hardening