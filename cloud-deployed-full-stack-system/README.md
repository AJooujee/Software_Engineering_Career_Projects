# Cloud Operations Platform

A cloud-ready full-stack application for monitoring services, managing operational incidents, and controlling access through authenticated user roles.

This portfolio project demonstrates full-stack software engineering with React, React Router, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Argon2 password hashing, JSON Web Tokens, role-based access control, responsive interface design, automated testing, and environment-based configuration.

## Current Status

**Phase 6 - Dashboard, Filtering, and Audit History: Complete**

The application now provides live operational dashboard metrics, Incident search and filtering, and immutable administrator-only audit history. Incident and user mutations record safe actor snapshots and field-level change metadata in the same database transaction as the business operation.

Phase 6 is covered by 57 automated tests across the backend and frontend, production frontend build validation, Alembic schema validation, and manual role-aware browser verification.

## Current Features

- Responsive React single-page application
- React Router navigation with public and protected route groups
- Registration and login interfaces connected to FastAPI
- Session-scoped JWT storage with automatic session validation
- Authenticated and role-restricted route guards
- Role-aware navigation for viewers, operators, and administrators
- Live operational dashboard metrics for authenticated users
- Incident status and severity distributions
- Active-Incident and affected-service metrics
- Administrator-only recent audit activity
- Paginated Incident queue with selected-record details
- Incident search across title, description, and service
- Incident filtering by status, severity, and service name
- Applied-filter state with clearing and filtered empty-state feedback
- Viewer read-only Incident access
- Operator Incident creation and editing
- Administrator Incident deletion with explicit confirmation
- Loading, empty, success, retry, and busy states
- Shared frontend API client with structured error handling
- PostgreSQL 18 with SQLAlchemy 2 and Alembic
- Persistent User, Incident, and AuditEvent models
- Immutable audit records for Incident and user mutations
- Safe actor snapshots and field-level change metadata
- Atomic business mutations and audit-event creation
- Argon2 password hashing and signed JWT access tokens
- Database-backed role and active-account enforcement
- Administrator user, role, and account-status management
- Administrator self-lockout protection
- Interactive Swagger API documentation
- Isolated backend and frontend automated tests
- Reproducible Python and Node dependencies
- Production frontend build command

## Technology Stack

### Frontend

- React 19
- React Router 8
- Vite 8
- Vitest 5
- React Testing Library
- Testing Library User Event
- Jest DOM matchers
- jsdom
- JavaScript
- Responsive CSS
- Node.js 24

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic and Pydantic Settings
- SQLAlchemy 2
- Alembic
- Psycopg 3
- pwdlib with Argon2
- PyJWT
- Email Validator
- Python Multipart
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
|   |   |-- api/routes/
|   |   |   |-- audit_events.py
|   |   |   |-- auth.py
|   |   |   |-- dashboard.py
|   |   |   |-- incidents.py
|   |   |   `-- users.py
|   |   |-- cli/bootstrap_admin.py
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |   |-- audit_event.py
|   |   |   |-- incident.py
|   |   |   `-- user.py
|   |   |-- repositories/
|   |   |   |-- audit_events.py
|   |   |   |-- dashboard.py
|   |   |   |-- incidents.py
|   |   |   `-- users.py
|   |   |-- schemas/
|   |   |   |-- audit_event.py
|   |   |   |-- dashboard.py
|   |   |   |-- incident.py
|   |   |   `-- user.py
|   |   |-- services/
|   |   |   |-- audit_events.py
|   |   |   |-- auth.py
|   |   |   |-- dashboard.py
|   |   |   `-- incidents.py
|   |   `-- main.py
|   |-- migrations/versions/
|   |   |-- 2ef9cb82e708_create_incidents_table.py
|   |   |-- 6b0140f7a01f_create_users_table.py
|   |   `-- 7c9e4b2a6d10_create_audit_events_table.py
|   `-- tests/
|       |-- test_audit_events.py
|       |-- test_auth.py
|       |-- test_dashboard.py
|       |-- test_health.py
|       |-- test_incident_filters.py
|       |-- test_incidents.py
|       `-- test_users.py
|-- docs/architecture.md
|-- frontend/
|   `-- src/
|       |-- api/
|       |   |-- audit-events.js
|       |   |-- audit-events.test.js
|       |   |-- dashboard.js
|       |   |-- dashboard.test.js
|       |   |-- incidents.js
|       |   `-- incidents.test.js
|       |-- auth/
|       |-- components/
|       |   |-- IncidentFilters.jsx
|       |   |-- IncidentList.jsx
|       |   |-- IncidentDetails.jsx
|       |   |-- IncidentForm.jsx
|       |   `-- IncidentDeleteDialog.jsx
|       |-- layouts/
|       |-- pages/
|       |   |-- DashboardPage.jsx
|       |   |-- DashboardPage.test.jsx
|       |   |-- IncidentsPage.jsx
|       |   |-- IncidentsPage.test.jsx
|       |   `-- IncidentsPage.filters.test.jsx
|       |-- routes/
|       |-- App.jsx
|       |-- index.css
|       `-- main.jsx
|-- .env.example
|-- .gitignore
`-- README.md
```

## Environment Configuration

Create a private local environment file from the provided template:

```powershell
Copy-Item .env.example .env
```

The real `.env` file is excluded from Git and must never be committed.

The application uses these variables:

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
| `JWT_SECRET_KEY` | Signs and validates access tokens |
| `JWT_ALGORITHM` | Selects the permitted JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Controls access-token lifetime |
| `JWT_ISSUER` | Identifies the service issuing tokens |
| `JWT_AUDIENCE` | Identifies the intended token consumer |

Generate a private random JWT secret after creating `.env`:

```powershell
$secretBytes = New-Object byte[] 32
$randomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($secretBytes)
$randomGenerator.Dispose()
$jwtSecret = [Convert]::ToBase64String($secretBytes)

$privateEnvironment = Get-Content .\.env -Raw
$privateEnvironment = $privateEnvironment.Replace(
    "replace-with-a-secure-random-secret-at-least-32-characters",
    $jwtSecret
)

Set-Content -Path .\.env -Value $privateEnvironment -Encoding utf8
Remove-Variable jwtSecret, secretBytes
```

Do not print or commit the generated secret.

## Local Development

### 1. Start PostgreSQL

Create the PostgreSQL container the first time:

```powershell
docker run `
    --name cloud-operations-postgres `
    -e POSTGRES_DB=cloud_operations `
    -e POSTGRES_USER=cloud_ops `
    -e POSTGRES_PASSWORD=cloud_ops_password `
    -p 5434:5432 `
    -v cloud-operations-postgres-data:/var/lib/postgresql `
    -d postgres:18-alpine
```

For later development sessions:

```powershell
docker start cloud-operations-postgres
```

Verify database readiness:

```powershell
docker exec cloud-operations-postgres `
    pg_isready `
    -U cloud_ops `
    -d cloud_operations
```

### 2. Install and Migrate the Backend

From the project directory:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Verify the current migration:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

### 3. Bootstrap an Administrator

Create the first administrator without putting the password in shell history:

```powershell
.\.venv\Scripts\python.exe -m app.cli.bootstrap_admin `
    --email "admin@example.com" `
    --full-name "Cloud Operations Administrator"
```

The command securely prompts for the password and confirmation.

It can also promote an existing registered user:

```powershell
.\.venv\Scripts\python.exe -m app.cli.bootstrap_admin `
    --email "existing.user@example.com"
```

The command is idempotent and also reactivates a disabled administrator account.

### 4. Start the Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend is available at:

```text
http://127.0.0.1:8000
```

Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### 5. Start the Frontend

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

## Frontend Routes

| Route | Access | Purpose |
|---|---|---|
| `/login` | Signed-out users | Authenticates an existing account |
| `/register` | Signed-out users | Creates and authenticates a viewer account |
| `/dashboard` | Authenticated | Displays operational metrics and role context |
| `/incidents` | Authenticated | Provides filtered, paginated, role-aware Incident management |
| `/users` | Admin | Provides administrator user management |
| `/forbidden` | Authenticated | Explains insufficient route permissions |
| Unmatched route | Any visitor | Displays the not-found page |

The dashboard presents live Incident totals, active and critical counts, affected services, and status and severity distributions. Administrators additionally receive the latest audit history.

## Frontend Incident Workflow

The Incident workspace loads paginated records from the protected API, automatically selects an available record, and presents its severity, lifecycle status, service, description, timestamps, and identifier.

Users can search Incident titles, descriptions, and service names. They can also filter by lifecycle status, severity, and exact service name. Draft values do not change the queue until **Apply filters** is selected. Applying or clearing filters returns pagination to the first page.

| Role | Available frontend actions |
|---|---|
| Viewer | Refresh, filter, paginate, select, and inspect Incidents |
| Operator | All viewer actions plus create and edit |
| Administrator | All operator actions plus confirmed deletion |

Successful mutations synchronize the list and selected detail. Unmatched filters display a dedicated filtered-results empty state. Recoverable failures provide retry actions, while FastAPI independently validates every bearer token, active account, and required role.

## Production Frontend Build

Create an optimized production build from the `frontend` directory:

```powershell
npm run build
```

Vite writes the generated application to `frontend/dist`. The directory is excluded from Git because it is reproducible from the committed source and dependency lock file.

## Frontend Authentication Workflow

The frontend stores its access token in browser `sessionStorage`. The token is therefore shared only within the current browser tab and is removed when the tab session ends or the user signs out.

When the application starts with a stored token:

1. `AuthProvider` loads the token from session storage.
2. The frontend requests `/api/auth/me`.
3. A valid response restores the authenticated user.
4. A `401` or `403` response removes the rejected token.
5. A network failure displays a retryable session error without treating it as valid authentication.

During login, the frontend requests an access token and then loads the current profile. The token is persisted only after both requests succeed.

Successful registration creates a viewer account and automatically performs the login workflow.

Frontend route guards improve navigation and presentation, but they are not the security boundary. FastAPI validates the token, active-account status, and required role for every protected API request.

## Backend Authentication Workflow

### Register

New accounts are assigned the `viewer` role:

```http
POST /api/auth/register
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "full_name": "Example User",
  "password": "SecurePassword123!"
}
```

Passwords must contain between 12 and 128 characters.

### Login

The token endpoint accepts OAuth2 form data. The `username` field contains the user's email address:

```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded
```

A successful login returns:

```json
{
  "access_token": "signed-jwt-value",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Authenticated Requests

Send the access token using the Authorization header:

```text
Authorization: Bearer signed-jwt-value
```

The current profile is available through:

```http
GET /api/auth/me
```

JWTs contain the user's identifier but do not contain an authorization role. The backend loads the current user from PostgreSQL for every authenticated request. Role changes and account deactivation therefore apply immediately to existing tokens.

## Authorization Roles

| Operation | Viewer | Operator | Admin |
|---|---:|---:|---:|
| View dashboard metrics | Yes | Yes | Yes |
| View audit history | No | No | Yes |
| Read and filter incidents | Yes | Yes | Yes |
| Create incidents | No | Yes | Yes |
| Update incidents | No | Yes | Yes |
| Delete incidents | No | No | Yes |
| List users | No | No | Yes |
| Change user roles | No | No | Yes |
| Activate or disable users | No | No | Yes |

Administrators cannot remove their own admin role or disable their own account. Audit-history authorization is enforced by FastAPI even for direct API requests.

## Database Migrations

Run migration commands from the `backend` directory.

| Revision | Change |
|---|---|
| `2ef9cb82e708` | Creates the Incident table, constraints, and indexes |
| `6b0140f7a01f` | Creates the User table, role constraint, and indexes |
| `7c9e4b2a6d10` | Creates the immutable audit-events table and indexes |

Apply pending migrations with `.\.venv\Scripts\python.exe -m alembic upgrade head`, display the current revision with `alembic current`, and verify model consistency with `alembic check`. Autogenerated migrations must be reviewed before they are applied.

## Automated Testing

### Backend Tests

Backend integration tests use isolated SQLite in-memory storage and do not modify PostgreSQL development data.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

Current expected result: **26 passed**.

Coverage includes authentication, database-backed authorization, Incident CRUD and filters, dashboard aggregation, administrator-only audit access, mutation audit records, actor snapshots, field-level changes, transaction rollback, and suppression of failed or no-op audit events.

### Frontend Tests

```powershell
cd frontend
npm test
npm run build
```

Current expected result: **9 test files and 31 tests passed**, followed by a successful Vite production build.

Coverage includes session state, route guards, API clients, Incident role workflows, pagination, filters, filtered empty states, dashboard metrics, administrator audit presentation, and recoverable request failures.

Together, the backend and frontend suites provide **57 automated tests**.

## API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` | Public | Confirms that the backend is running |
| GET | `/health` | Public | Returns backend health status |
| POST | `/api/auth/register` | Public | Registers a viewer account |
| POST | `/api/auth/token` | Public | Authenticates credentials and returns a JWT |
| GET | `/api/auth/me` | Authenticated | Returns the current user |
| GET | `/api/dashboard/summary` | Authenticated | Returns operational metrics and distributions |
| GET | `/api/audit-events` | Admin | Lists immutable audit events with pagination |
| GET | `/api/users` | Admin | Lists registered users |
| GET | `/api/users/{user_id}` | Admin | Retrieves one user |
| PATCH | `/api/users/{user_id}/role` | Admin | Changes a role and records an audit event |
| PATCH | `/api/users/{user_id}/status` | Admin | Changes account status and records an audit event |
| POST | `/api/incidents` | Operator, Admin | Creates an Incident and audit event |
| GET | `/api/incidents` | Authenticated | Lists Incidents with pagination and filters |
| GET | `/api/incidents/{incident_id}` | Authenticated | Retrieves one Incident |
| PATCH | `/api/incidents/{incident_id}` | Operator, Admin | Updates an Incident and records changed fields |
| DELETE | `/api/incidents/{incident_id}` | Admin | Deletes an Incident and retains an audit snapshot |
| GET | `/docs` | Public | Opens interactive API documentation |

The Incident list accepts `offset`, `limit`, `search`, `status`, `severity`, and `service_name` query parameters.

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

## Security Design

- Passwords are hashed with Argon2 and never stored or returned as plain text.
- JWT validation verifies algorithm, expiration, issuer, and audience.
- Roles and account status are reloaded from PostgreSQL for authenticated requests.
- Public registration cannot select an elevated role.
- Administrators cannot demote or disable their own account.
- Browser tokens use session storage and rejected tokens are removed.
- Frontend route guards never replace backend authorization.
- Dashboard data requires authentication; audit history requires administrator access.
- Audit records are immutable through the application API.
- Audit records retain safe actor and resource snapshots.
- Audit metadata excludes passwords, password hashes, tokens, and secrets.
- Business mutations and audit events commit or roll back atomically.
- Failed and no-op mutations do not create misleading audit records.
- Test credentials and databases are isolated from development data.

Session storage does not protect a token from malicious JavaScript executing in the same page. Production deployment must maintain strict script controls and avoid unsafe HTML injection.

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation and health integration | Complete |
| 2 | PostgreSQL database and backend CRUD API | Complete |
| 3 | Authentication and role-based access control | Complete |
| 4 | Frontend routing and application layout | Complete |
| 5 | Incident management workflow | Complete |
| 6 | Dashboard, filtering, and audit history | Complete |
| 7 | Docker and local service integration | Planned |
| 8 | Automated testing and CI/CD | Planned |
| 9 | Cloud deployment and observability | Planned |

## Author

**AJ C Pipattanakun**

Software Engineering Portfolio Project
