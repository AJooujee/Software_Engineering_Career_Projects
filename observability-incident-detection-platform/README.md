# Observability & Incident Detection Platform

A backend platform for collecting operational telemetry, monitoring service
health, detecting abnormal behavior, and managing incidents.

The project is being developed incrementally to demonstrate backend engineering,
observability, automated testing, and production-oriented system design.


## Current Status

Phase 7: Metrics Dashboards and Distributed Tracing

Implemented:

- FastAPI application foundation
- Environment-based configuration
- Request ID and structured JSON logging
- Metric, log, and event telemetry schemas
- Batch telemetry ingestion API
- Telemetry query API with service, environment, type, and source filters
- Deterministic rule-based anomaly detection engine
- Metric threshold, log severity, and event severity rules
- Transactional anomaly persistence linked to source telemetry
- Filterable anomaly query API
- Time-range filtering and offset-based pagination
- Newest-first telemetry ordering
- PostgreSQL persistent telemetry storage
- Monitored service registry
- SQLAlchemy asynchronous ORM and repository layer
- Atomic database transactions and rollback
- Alembic schema migrations
- Application and database health endpoints
- Isolated database integration tests
- GitHub Actions with PostgreSQL migration validation
- Automatic incident creation for critical anomalies
- Atomic telemetry, anomaly, and incident persistence
- Incident lifecycle transitions: open, acknowledged, and resolved
- Filterable incident query and detail APIs
- Incident ownership and resolution audit timestamps
- Time-window incident correlation by service and environment
- Deterministic and explainable root-cause scoring
- Probable root-cause confidence and evidence reasons
- Atomic correlation and incident-link persistence
- Prevention of incident reuse across correlations
- Filterable correlation query and detail APIs
- SQLite foreign-key enforcement in integration tests
- W3C-compatible distributed trace and span schemas
- Atomic multi-service trace span ingestion
- Persistent PostgreSQL trace span storage
- Parent-child span hierarchy preservation
- Cross-service distributed trace reconstruction
- Per-span and trace-level duration calculation
- Duplicate trace span detection and conflict handling
- Metric dashboard aggregation from persisted telemetry
- Service, environment, source, metric, and time-window filtering
- Minimum, maximum, average, p95, and latest metric statistics
- Chronologically ordered dashboard time-series points
- Metric unit consistency validation
- PostgreSQL and SQLite-compatible dashboard querying

Documentation:

- [Telemetry Ingestion](docs/telemetry-ingestion.md)
- [Telemetry Querying](docs/telemetry-querying.md)
- [Rule-Based Anomaly Detection](docs/anomaly-detection.md)
- [Incident Lifecycle Management](docs/incident-lifecycle.md)
- [Database Persistence and Service Registry](docs/database-persistence.md)
- [Event Correlation and Root-Cause Analysis](docs/event-correlation.md)
- [Distributed Tracing](docs/distributed-tracing.md)
- [Metrics Dashboard](docs/metrics-dashboard.md)

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
- Telemetry query: `GET http://127.0.0.1:8000/api/v1/telemetry`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`
- Detected anomalies: `GET http://127.0.0.1:8000/api/v1/anomalies`
- Incidents: `GET http://127.0.0.1:8000/api/v1/incidents`
- Incident details: `GET http://127.0.0.1:8000/api/v1/incidents/{incident_id}`
- Acknowledge incident: `PATCH http://127.0.0.1:8000/api/v1/incidents/{incident_id}/acknowledge`
- Resolve incident: `PATCH http://127.0.0.1:8000/api/v1/incidents/{incident_id}/resolve`
- Analyze correlations: `POST http://127.0.0.1:8000/api/v1/correlations/analyze`
- Query correlations: `GET http://127.0.0.1:8000/api/v1/correlations`
- Correlation details: `GET http://127.0.0.1:8000/api/v1/correlations/{correlation_id}`
- Trace span ingestion: `POST http://127.0.0.1:8000/api/v1/traces`
- Distributed trace details: `GET http://127.0.0.1:8000/api/v1/traces/{trace_id}`
- Metric dashboard summary: `GET http://127.0.0.1:8000/api/v1/dashboard/metrics/summary`

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
- [x] Phase 4: Rule-based anomaly and incident detection
- [x] Phase 5: Alerting and incident lifecycle management
- [x] Phase 6: Event correlation and root-cause analysis
- [x] Phase 7: Metrics dashboards and distributed tracing
- [ ] Phase 8: Containerization, CI/CD, security, and production hardening