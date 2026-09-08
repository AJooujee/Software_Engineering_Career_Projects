# Cloud Operations Platform

A cloud-ready full-stack application for monitoring services, managing operational incidents, and controlling access through authenticated user roles.

This portfolio project demonstrates full-stack software engineering with React, React Router, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Argon2 password hashing, JSON Web Tokens, role-based access control, responsive interface design, multi-stage containers, Nginx reverse proxying, Docker Compose, GitHub Actions CI/CD, GitHub Container Registry delivery, Azure Container Apps, Azure Database for PostgreSQL, Bicep infrastructure as code, centralized logging, automated testing, and environment-based configuration.

## Current Status

**Phase 9 - Cloud Deployment and Observability: Complete**

The production stack is deployed in Azure North Central US from immutable images built at commit `32ba84f1d310410fda315c9e348acc8fb0ab87d3`. The public frontend uses Azure Container Apps HTTPS ingress and proxies same-origin API traffic to an internal FastAPI Container App backed by Azure Database for PostgreSQL Flexible Server.

**Live application:** [Cloud Operations Platform](https://frontend-bdo5hkkvipb3s.victoriousforest-190ae510.northcentralus.azurecontainerapps.io)

The release used a provider validation and fresh ARM what-if before deployment. The what-if predicted nine creates and zero deletes. Infrastructure provisioning, the one-shot Alembic migration, administrator bootstrap, authenticated UI verification, production-stack smoke validation, and centralized-log validation all completed successfully.

Log Analytics receives Container Apps console and system logs. The production validation window recorded 192 structured backend request events with zero application error-like records and zero Azure system errors for either application. The deployment is a cost-controlled portfolio environment and availability is best-effort.

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
- Secure, idempotent administrator bootstrap with audited role changes
- Four-service Docker Compose application stack
- Health-gated one-shot Alembic migration service
- Multi-stage backend and frontend container images
- Dedicated non-root runtime users
- Unprivileged Nginx production frontend and reverse proxy
- SPA fallback, immutable asset caching, and response security headers
- Internal database network and loopback-only published host ports
- Persistent named PostgreSQL volume
- Interactive Swagger API documentation through the frontend proxy
- Repository-scoped GitHub Actions triggers for the monorepo
- Independent backend and frontend validation gates
- Production-like Compose integration and smoke validation
- Least-privilege GitHub Container Registry delivery from `main`
- Commit-addressable and rolling container-image tags
- Automatic cancellation of superseded branch runs
- Isolated backend and frontend automated tests
- Reproducible Python and Node dependencies
- Production frontend build command
- Modular Bicep infrastructure for monitoring, database, and Container Apps
- Azure Container Apps consumption deployment with scale-to-zero web workloads
- Azure Database for PostgreSQL Flexible Server with TLS
- One-shot Azure Container Apps migration job
- Centralized application and platform logs in Log Analytics
- Structured JSON request logs with safe request correlation
- Production liveness, readiness, proxy, asset, header, and log validation

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
- HTTPX

### Database, Container, Cloud, and Delivery Infrastructure

- PostgreSQL 18 Alpine for local development
- Docker and Docker Compose
- Multi-stage Docker builds
- Nginx Unprivileged 1.30 Alpine
- Docker health checks, dependency conditions, and named volumes
- Isolated Compose edge and internal data networks
- GitHub Actions with monorepo path filters and concurrency control
- GitHub Container Registry
- Commit-SHA and rolling `main` image tags
- Azure Resource Manager and Bicep
- Azure Container Apps consumption environment
- Azure Container Apps Job for Alembic migrations
- Azure Database for PostgreSQL Flexible Server 18
- Azure Log Analytics workspace
- SQLite in-memory test database
- Environment variables and managed runtime secrets

### Production Infrastructure

- Public HTTPS Nginx and React Container App
- Internal-ingress FastAPI Container App
- Burstable `Standard_B1ms` PostgreSQL with 32 GB storage and high availability disabled
- Container Apps minimum replicas of zero and maximum replicas of one
- Log Analytics retention of 30 days with a 1 GB daily ingestion cap
- Manually approved deployment from immutable GHCR commit-SHA images

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
|   |   |-- repositories/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- main.py
|   |-- migrations/versions/
|   |-- tests/
|   |   |-- test_audit_events.py
|   |   |-- test_auth.py
|   |   |-- test_bootstrap_admin.py
|   |   |-- test_dashboard.py
|   |   |-- test_health.py
|   |   |-- test_incident_filters.py
|   |   |-- test_incidents.py
|   |   `-- test_users.py
|   |-- .dockerignore
|   `-- Dockerfile
|-- docs/
|   |-- architecture.md
|   `-- production-release.md
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- auth/
|   |   |-- components/
|   |   |-- layouts/
|   |   |-- pages/
|   |   |-- routes/
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- .dockerignore
|   |-- Dockerfile
|   `-- nginx.conf
|-- infra/
|   |-- modules/
|   |   |-- container-apps.bicep
|   |   |-- database.bicep
|   |   `-- monitoring.bicep
|   |-- parameters/portfolio.bicepparam
|   |-- main.bicep
|   `-- README.md
|-- scripts/
|   `-- ci_smoke.py
|-- .env.example
|-- .gitignore
|-- compose.yaml
`-- README.md
```

The monorepo-level workflow is stored at `../.github/workflows/cloud-operations-ci.yml`. Keeping it at the Git repository root allows GitHub Actions discovery while path filters isolate it from the other portfolio projects.

## Environment Configuration

Create a private local environment file from the provided template:

```powershell
Copy-Item .env.example .env
```

The real `.env` file is excluded from Git and must never be committed. Replace the sample database password and JWT secret before starting the Compose stack.

| Variable | Purpose |
|---|---|
| `APP_ENV` | Selects the application runtime environment |
| `BACKEND_HOST` | Defines the manually run backend host |
| `BACKEND_PORT` | Defines the manually run backend port |
| `VITE_API_BASE_URL` | Points a manually run Vite frontend to the backend API |
| `POSTGRES_DB` | Defines the PostgreSQL database name |
| `POSTGRES_USER` | Defines the PostgreSQL user |
| `POSTGRES_PASSWORD` | Supplies the required database password |
| `POSTGRES_PORT` | Exposes PostgreSQL for manual local development |
| `DATABASE_URL` | Provides the manual SQLAlchemy database connection URL |
| `JWT_SECRET_KEY` | Supplies the required token-signing secret |
| `JWT_ALGORITHM` | Selects the permitted JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Controls access-token lifetime |
| `JWT_ISSUER` | Identifies the service issuing tokens |
| `JWT_AUDIENCE` | Identifies the intended token consumer |
| `COMPOSE_FRONTEND_PORT` | Publishes Nginx to loopback; defaults to `8080` |
| `COMPOSE_BACKEND_PORT` | Publishes FastAPI to loopback; defaults to `8001` |

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

## Docker Compose

Docker Compose is the primary full-stack runtime. From the project root, create `.env`, replace its sample secrets, and then validate and start the stack:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

The services start in dependency order:

1. PostgreSQL starts and passes `pg_isready`.
2. The one-shot migration service applies `alembic upgrade head` and exits successfully.
3. FastAPI starts only after PostgreSQL is healthy and migration completes.
4. Nginx starts after the backend is healthy.

Open the production application at `http://127.0.0.1:8080`. Swagger documentation is proxied at `http://127.0.0.1:8080/docs`, and the backend health endpoint is also available directly at `http://127.0.0.1:8001/health`.

Create or promote an administrator without placing a password in shell history:

```powershell
docker compose exec backend python -m app.cli.bootstrap_admin `
    --email "admin@example.com" `
    --full-name "Cloud Operations Administrator"
```

Useful lifecycle commands:

```powershell
docker compose logs --follow
docker compose down
```

`docker compose down` preserves the named PostgreSQL volume. Use `docker compose down --volumes` only when intentionally deleting local database data.

## Manual Local Development

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

The frontend Dockerfile performs the same build with `npm ci` in a Node stage, then copies only `dist` into an unprivileged Nginx runtime image. Nginx serves browser-managed routes through an SPA fallback, proxies API and documentation routes to FastAPI, disables caching for the application entry point, and applies long-lived immutable caching to fingerprinted assets.

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

Backend integration tests use isolated SQLite in-memory storage and do not modify PostgreSQL development or production data.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

The suite covers authentication, database-backed authorization, Incident CRUD and filters, dashboard aggregation, administrator-only audit access, mutation audit records, actor snapshots, field-level changes, transaction rollback, administrator bootstrap, request IDs, structured request logging, and suppression of sensitive query values.

### Frontend Tests

```powershell
cd frontend
npm test
npm run build
```

Current expected result: **9 test files and 31 tests passed**, followed by a successful Vite production build.

Coverage includes session state, route guards, API clients, Incident role workflows, pagination, filters, filtered empty states, dashboard metrics, administrator audit presentation, and recoverable request failures.

The CI workflow executes the complete backend and frontend suites. It also validates the Alembic migration graph, reproducible dependency installation, production output, Compose rendering and image builds, migration exit state, non-root identities, service health, proxy behavior, SPA fallback, request correlation, required API discovery, security headers, and immutable asset caching.

## CI/CD Automation

The repository-level `Cloud Operations CI/CD` workflow is path-scoped to `cloud-deployed-full-stack-system/**` and its own workflow file. Unrelated portfolio projects therefore do not start this pipeline.

| Trigger | Validation behavior | Image publishing |
|---|---|---|
| Push to `feature/**` | Runs all validation gates | Skipped |
| Pull request targeting `main` | Runs all validation gates | Skipped |
| Manual dispatch | Runs all validation gates | Skipped |
| Direct push or merged pull request on `main` | Runs all validation gates | Publishes after every gate passes |

| Job | Responsibility |
|---|---|
| Backend tests and migration graph | Installs pinned Python dependencies, compiles source and tests, verifies one Alembic head, and runs the complete Pytest suite |
| Frontend tests and production build | Uses `npm ci`, runs 31 tests, builds Vite output, and verifies the entry point and JavaScript bundle |
| Compose end-to-end validation | Builds and starts the production-like stack, verifies migration and runtime identities, and runs `scripts/ci_smoke.py` |
| Publish deployment images to GHCR | Authenticates with the job-scoped `GITHUB_TOKEN` and publishes only from `main` |

The delivery job publishes:

- `ghcr.io/ajooujee/cloud-operations-backend:<commit-sha>`
- `ghcr.io/ajooujee/cloud-operations-backend:main`
- `ghcr.io/ajooujee/cloud-operations-frontend:<commit-sha>`
- `ghcr.io/ajooujee/cloud-operations-frontend:main`

The commit-SHA tags provide immutable deployment references, while `main` identifies the latest validated main-branch build. Both images carry OCI source and revision labels. No personal access token or repository secret is required for registry authentication.

Run the smoke test against the default local Compose ports with:

```powershell
.\backend\.venv\Scripts\python.exe scripts\ci_smoke.py
```

## Azure Production Deployment

| Item | Production value |
|---|---|
| Public application | [Cloud Operations Platform](https://frontend-bdo5hkkvipb3s.victoriousforest-190ae510.northcentralus.azurecontainerapps.io) |
| Azure region | `northcentralus` |
| Resource group | `rg-cloud-operations-portfolio-northcentralus` |
| Release source | `32ba84f1d310410fda315c9e348acc8fb0ab87d3` |
| Frontend | `frontend-bdo5hkkvipb3s` with external HTTPS ingress |
| Backend | `backend-bdo5hkkvipb3s` with internal ingress |
| Migration job | `migration-bdo5hkkvipb3s` |
| PostgreSQL | `pg-cloudops-portfolio-bdo5hkkvipb3s` |
| Log Analytics | `log-cloudops-portfolio-bdo5hkkvipb3s` |

The GitHub Actions workflow validates the code and publishes immutable images. Azure deployment remains a deliberate, manually approved release step: validate providers, review ARM what-if output, authorize resource creation, run the migration job, bootstrap the first administrator, execute the production smoke test, and inspect centralized logs.

Production verification confirmed direct and proxied liveness and readiness, database availability, request correlation, SPA fallback, JavaScript delivery, restrictive response headers, immutable asset caching, required API paths, authenticated administrator access, and centralized application and Azure system logs. See [Production Release Evidence](docs/production-release.md) for the complete release record and cost boundary.
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
- Audit metadata excludes passwords, password hashes, tokens, and secrets.
- Business mutations and audit events commit or roll back atomically.
- Failed and no-op mutations do not create misleading audit records.
- Compose refuses to render without `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`.
- PostgreSQL is isolated on an internal network and has no published host port.
- Published frontend and backend ports bind only to `127.0.0.1`.
- Backend and frontend runtime images use dedicated non-root users.
- FastAPI waits for both database health and successful migration completion.
- Nginx sends `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` on pages, assets, and proxied responses.
- Fingerprinted assets use immutable caching while the SPA entry point uses no-cache behavior.
- Test credentials and databases are isolated from development data.
- GitHub Actions defaults to read-only repository contents.
- Registry write access exists only in the `main` image-publishing job.
- Pull requests and feature branches cannot execute the registry delivery path.
- CI Compose credentials are disposable runner-local values, not production secrets.
- Compose diagnostics run on failure and isolated CI volumes are always removed.
- Published images include source-repository and commit-revision labels.

Session storage does not protect a token from malicious JavaScript executing in the same page. The Azure deployment uses HTTPS ingress, Container Apps secrets, a restrictive Content Security Policy, production-specific origin configuration, immutable image references, and a manually reviewed release. The cost-first database profile uses a public PostgreSQL endpoint with mandatory TLS and an Azure-services firewall rule; a paid production environment should replace that trade-off with private networking and managed database identity.

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation and health integration | Complete |
| 2 | PostgreSQL database and backend CRUD API | Complete |
| 3 | Authentication and role-based access control | Complete |
| 4 | Frontend routing and application layout | Complete |
| 5 | Incident management workflow | Complete |
| 6 | Dashboard, filtering, and audit history | Complete |
| 7 | Docker and local service integration | Complete |
| 8 | Automated testing and CI/CD | Complete |
| 9 | Cloud deployment and observability | Complete |

## Author

**AJ C Pipattanakun**

Software Engineering Portfolio Project
