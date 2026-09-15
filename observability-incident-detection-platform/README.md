# Observability & Incident Detection Platform

A backend platform for collecting operational telemetry, monitoring service
health, detecting abnormal behavior, and managing incidents.

The project is being developed incrementally to demonstrate backend engineering,
observability, automated testing, and production-oriented system design.

## Current Status

Phase 3: Persistent Storage and Service Registry

Implemented:

- FastAPI application foundation
- Environment-based configuration
- Request ID and structured JSON logging
- Metric, log, and event telemetry schemas
- Batch telemetry ingestion API
- PostgreSQL persistent telemetry storage
- Monitored service registry
- SQLAlchemy asynchronous ORM and repository layer
- Atomic database transactions and rollback
- Alembic schema migrations
- Application and database health endpoints
- Isolated database integration tests
- GitHub Actions with PostgreSQL migration validation

Documentation:

- [Telemetry Ingestion](docs/telemetry-ingestion.md)
- [Database Persistence and Service Registry](docs/database-persistence.md)

## Technology Stack

- Python 3.12+
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2
- asyncpg
- Alembic
- Docker Compose
- Pydantic Settings
- Pytest and pytest-asyncio
- HTTPX2
- Ruff
- GitHub Actions

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

- Application health: `GET http://127.0.0.1:8000/health`
- Database health: `GET http://127.0.0.1:8000/health/db`
- Register service: `POST http://127.0.0.1:8000/api/v1/services`
- List services: `GET http://127.0.0.1:8000/api/v1/services`
- Get service: `GET http://127.0.0.1:8000/api/v1/services/{service_id}`
- Telemetry ingestion: `POST http://127.0.0.1:8000/api/v1/telemetry`
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


## Database Setup

Create the local environment file:

```powershell
Copy-Item .env.example .env
```


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
- [x] Phase 3: Persistent telemetry storage and service registry
- [ ] Phase 4: Rule-based anomaly and incident detection
- [ ] Phase 5: Alerting and incident lifecycle management
- [ ] Phase 6: Event correlation and root-cause analysis
- [ ] Phase 7: Metrics dashboards and distributed tracing
- [ ] Phase 8: Containerization, CI/CD, security, and production hardening