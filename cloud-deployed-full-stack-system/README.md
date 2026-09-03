# Cloud Operations Platform

A cloud-ready full-stack application for monitoring services, managing operational incidents, and displaying system health through a single user interface.

This portfolio project demonstrates full-stack software engineering with React, FastAPI, PostgreSQL, SQLAlchemy, Alembic migrations, layered backend architecture, automated testing, and environment-based configuration.

## Current Status

**Phase 2 - PostgreSQL Database and Backend CRUD API: Complete**

The application now supports persistent incident management through a validated REST API backed by PostgreSQL.

## Current Features

- React single-page frontend
- FastAPI REST API
- Live frontend-to-backend health check
- PostgreSQL 18 development database
- SQLAlchemy 2 object-relational mapping
- Alembic database migrations
- Incident create, list, retrieve, update, and delete operations
- UUID incident identifiers
- Incident status and severity validation
- Layered route, service, repository, and database architecture
- Environment-based application configuration
- Local CORS configuration
- Interactive Swagger API documentation
- Isolated automated API integration tests
- Reproducible Python and Node dependencies
- Production frontend build command

## Technology Stack

### Frontend

- React 19
- Vite 8
- JavaScript
- CSS
- Node.js 24

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic Settings
- SQLAlchemy 2
- Alembic
- Psycopg 3
- Pytest
- HTTPX2

### Database and Development Infrastructure

- PostgreSQL 18
- Docker
- SQLite in-memory test database
- Environment variables through `.env`

### Planned Infrastructure

- Docker Compose application networking
- GitHub Actions
- Cloud deployment
- Centralized logging
- Application monitoring

## Project Structure

```text
cloud-deployed-full-stack-system/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   `-- routes/
|   |   |       `-- incidents.py
|   |   |-- core/
|   |   |   `-- config.py
|   |   |-- db/
|   |   |   |-- base.py
|   |   |   `-- session.py
|   |   |-- models/
|   |   |   `-- incident.py
|   |   |-- repositories/
|   |   |   `-- incidents.py
|   |   |-- schemas/
|   |   |   `-- incident.py
|   |   |-- services/
|   |   |   `-- incidents.py
|   |   `-- main.py
|   |-- migrations/
|   |   |-- versions/
|   |   |   `-- 2ef9cb82e708_create_incidents_table.py
|   |   `-- env.py
|   |-- tests/
|   |   |-- conftest.py
|   |   |-- test_health.py
|   |   `-- test_incidents.py
|   |-- alembic.ini
|   `-- requirements.txt
|-- docs/
|   `-- architecture.md
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- index.html
|   |-- package.json
|   |-- package-lock.json
|   `-- vite.config.js
|-- .env.example
|-- .gitignore
`-- README.md
```

## Environment Configuration

Create the private local environment file from the provided template:

```powershell
Copy-Item .env.example .env
```

The development configuration includes:

| Variable | Purpose |
|---|---|
| `APP_ENV` | Selects the application runtime environment |
| `BACKEND_HOST` | Defines the local backend host |
| `BACKEND_PORT` | Defines the local backend port |
| `VITE_API_BASE_URL` | Points the frontend to the backend API |
| `POSTGRES_DB` | Defines the PostgreSQL database name |
| `POSTGRES_USER` | Defines the PostgreSQL development user |
| `POSTGRES_PASSWORD` | Defines the local database password |
| `POSTGRES_PORT` | Exposes PostgreSQL on local port 5434 |
| `DATABASE_URL` | Provides the SQLAlchemy database connection URL |

The real `.env` file is excluded from Git.

## Local Development

### 1. Start PostgreSQL

Create the local PostgreSQL container the first time:

```powershell
docker run --name cloud-operations-postgres -e POSTGRES_DB=cloud_operations -e POSTGRES_USER=cloud_ops -e POSTGRES_PASSWORD=cloud_ops_password -p 5434:5432 -v cloud-operations-postgres-data:/var/lib/postgresql -d postgres:18-alpine
```

For later development sessions, start the existing container:

```powershell
docker start cloud-operations-postgres
```

Verify database readiness:

```powershell
docker exec cloud-operations-postgres pg_isready -U cloud_ops -d cloud_operations
```

### 2. Start the Backend

From the project directory:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend is available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Start the Frontend

Open another terminal from the project directory:

```powershell
cd frontend
npm install
npm run dev
```

The frontend is available at:

```text
http://127.0.0.1:5173
```

## Database Migrations

Run migration commands from the `backend` directory.

Apply every pending migration:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Display the current database revision:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Check whether model metadata differs from the database:

```powershell
.\.venv\Scripts\python.exe -m alembic check
```

Create a migration after changing a database model:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe schema change"
```

Autogenerated migrations must be reviewed before they are applied.

## Automated Testing

Backend API integration tests use an isolated SQLite in-memory database. They do not modify the PostgreSQL development database.

Run the test suite from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Current expected result:

```text
5 passed
```

The suite verifies:

- Backend health response
- Local frontend CORS access
- Complete Incident CRUD lifecycle
- Missing Incident responses
- Request validation and pagination limits

## Production Frontend Build

Run from the `frontend` directory:

```powershell
npm run build
```

Vite generates optimized production files inside `frontend/dist`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Confirms that the backend API is running |
| GET | `/health` | Returns the backend service health status |
| POST | `/api/incidents` | Creates an operational incident |
| GET | `/api/incidents` | Lists incidents with pagination |
| GET | `/api/incidents/{incident_id}` | Retrieves one incident |
| PATCH | `/api/incidents/{incident_id}` | Updates selected incident fields |
| DELETE | `/api/incidents/{incident_id}` | Deletes an incident |
| GET | `/docs` | Opens interactive Swagger documentation |

## Incident Lifecycle Values

Supported severity values:

```text
low
medium
high
critical
```

Supported status values:

```text
open
investigating
resolved
closed
```

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation and health integration | Complete |
| 2 | PostgreSQL database and backend CRUD API | Complete |
| 3 | Authentication and role-based access control | Planned |
| 4 | Frontend routing and application layout | Planned |
| 5 | Incident management workflow | Planned |
| 6 | Dashboard, filtering, and audit history | Planned |
| 7 | Docker and local service integration | Planned |
| 8 | Automated testing and CI/CD | Planned |
| 9 | Cloud deployment and observability | Planned |

## Author

**AJ C Pipattanakun**

Software Engineering Portfolio Project
