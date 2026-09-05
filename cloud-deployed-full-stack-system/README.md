# Cloud Operations Platform

A cloud-ready full-stack application for monitoring services, managing operational incidents, and controlling access through authenticated user roles.

This portfolio project demonstrates full-stack software engineering with React, React Router, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Argon2 password hashing, JSON Web Tokens, role-based access control, responsive interface design, automated testing, and environment-based configuration.

## Current Status

**Phase 4 - Frontend Routing and Application Layout: Complete**

The application now provides responsive registration and login pages, session-based authentication state, protected React routes, role-aware navigation, authenticated workspace layouts, and a dashboard connected to the FastAPI backend.

## Current Features

- Responsive React single-page application
- React Router navigation with public and protected route groups
- Registration and login interfaces connected to FastAPI
- Session-scoped JWT access-token storage
- Automatic stored-session validation through `/api/auth/me`
- Public-only route protection for authentication pages
- Authenticated and role-restricted route guards
- Role-aware sidebar navigation for viewers, operators, and administrators
- Authenticated dashboard with live backend health status
- Responsive public authentication and private application layouts
- Forbidden-access and not-found pages
- Incident-permission summary based on the authenticated role
- Administrator-only user-management route
- Shared frontend API client with structured error handling
- PostgreSQL 18 development database
- SQLAlchemy 2 object-relational mapping
- Alembic database migrations
- Persistent User and Incident models
- Public user registration with a default viewer role
- Argon2 password hashing
- OAuth2 password-form authentication
- Signed JWT access tokens with expiration, issuer, and audience validation
- Current-user lookup from PostgreSQL on every authenticated request
- Viewer, operator, and administrator authorization roles
- Protected Incident create, list, retrieve, update, and delete operations
- Administrator user listing, role management, and account status management
- Protection against administrator self-demotion and self-deactivation
- Secure administrator bootstrap command
- Layered frontend and backend architecture
- Environment-based application configuration
- Local CORS configuration
- Interactive Swagger API documentation
- Isolated backend integration tests
- Frontend unit and route-guard tests
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
|   |   |-- api/
|   |   |   |-- dependencies/
|   |   |   |   `-- auth.py
|   |   |   `-- routes/
|   |   |       |-- auth.py
|   |   |       |-- incidents.py
|   |   |       `-- users.py
|   |   |-- cli/
|   |   |   `-- bootstrap_admin.py
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   `-- security.py
|   |   |-- db/
|   |   |   |-- base.py
|   |   |   `-- session.py
|   |   |-- models/
|   |   |   |-- incident.py
|   |   |   `-- user.py
|   |   |-- repositories/
|   |   |   |-- incidents.py
|   |   |   `-- users.py
|   |   |-- schemas/
|   |   |   |-- incident.py
|   |   |   `-- user.py
|   |   |-- services/
|   |   |   |-- auth.py
|   |   |   `-- incidents.py
|   |   `-- main.py
|   |-- migrations/
|   |   |-- versions/
|   |   |   |-- 2ef9cb82e708_create_incidents_table.py
|   |   |   `-- 6b0140f7a01f_create_users_table.py
|   |   `-- env.py
|   |-- tests/
|   |   |-- conftest.py
|   |   |-- test_auth.py
|   |   |-- test_health.py
|   |   |-- test_incidents.py
|   |   `-- test_users.py
|   |-- alembic.ini
|   `-- requirements.txt
|-- docs/
|   `-- architecture.md
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |   |-- auth.js
|   |   |   |-- auth.test.js
|   |   |   |-- client.js
|   |   |   `-- health.js
|   |   |-- auth/
|   |   |   |-- AuthContext.jsx
|   |   |   |-- token-storage.js
|   |   |   `-- token-storage.test.js
|   |   |-- components/
|   |   |   |-- PageHeader.jsx
|   |   |   `-- RouteStatus.jsx
|   |   |-- layouts/
|   |   |   |-- AppLayout.jsx
|   |   |   `-- AuthLayout.jsx
|   |   |-- pages/
|   |   |   |-- DashboardPage.jsx
|   |   |   |-- ForbiddenPage.jsx
|   |   |   |-- IncidentsPage.jsx
|   |   |   |-- LoginPage.jsx
|   |   |   |-- NotFoundPage.jsx
|   |   |   |-- RegisterPage.jsx
|   |   |   `-- UsersPage.jsx
|   |   |-- routes/
|   |   |   |-- ProtectedRoute.jsx
|   |   |   |-- PublicOnlyRoute.jsx
|   |   |   `-- RouteGuards.test.jsx
|   |   |-- test/
|   |   |   `-- setup.js
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
| `/dashboard` | Authenticated | Displays backend health and current access |
| `/incidents` | Authenticated | Displays role-specific Incident permissions |
| `/users` | Admin | Displays the administrator workspace |
| `/forbidden` | Authenticated | Explains insufficient route permissions |
| Unmatched route | Any visitor | Displays the not-found page |

Public-only guards redirect authenticated users away from the login and registration pages. Protected guards preserve the requested location and return signed-out users to it after successful authentication.

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
| Read incidents | Yes | Yes | Yes |
| Create incidents | No | Yes | Yes |
| Update incidents | No | Yes | Yes |
| Delete incidents | No | No | Yes |
| List users | No | No | Yes |
| Change user roles | No | No | Yes |
| Activate or disable users | No | No | Yes |

Administrators cannot remove their own admin role or disable their own account through the API.

## Database Migrations

Run migration commands from the `backend` directory.

Apply pending migrations:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Display the current revision:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Check model and database consistency:

```powershell
.\.venv\Scripts\python.exe -m alembic check
```

Create a migration after changing a model:

```powershell
.\.venv\Scripts\python.exe -m alembic revision `
    --autogenerate `
    -m "describe schema change"
```

Autogenerated migrations must be reviewed before they are applied.

## Automated Testing

### Backend Tests

Backend integration tests use an isolated SQLite in-memory database. They do not modify PostgreSQL development data and do not require Docker.

Run the suite from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Current expected result:

```text
18 passed
```

The backend suite verifies:

- Backend health and CORS behavior
- User registration and normalized email uniqueness
- Argon2 password storage and verification
- OAuth2 login and JWT authentication
- Missing, invalid, and disabled-account token handling
- Viewer, operator, and administrator Incident permissions
- Administrator user-management permissions
- Immediate application of role and status changes
- Privilege-escalation prevention
- Administrator self-lockout prevention
- Incident CRUD, validation, pagination, and missing-record responses

### Frontend Tests

Frontend tests run with Vitest, React Testing Library, Jest DOM matchers, and jsdom.

Run the suite from the `frontend` directory:

```powershell
npm test
```

Current expected result:

```text
3 test files passed
12 tests passed
```

The frontend suite verifies:

- Loading an absent session token
- Saving, restoring, and removing session tokens
- Public-only route behavior
- Signed-out protected-route redirects
- Authenticated protected-route access
- Role-restricted route redirects
- Registration payload normalization
- OAuth2 login form construction
- Bearer-token request headers
- Backend authentication error propagation

Validate the production frontend bundle with:

```powershell
npm run build
```

## API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` | Public | Confirms that the backend is running |
| GET | `/health` | Public | Returns backend health status |
| POST | `/api/auth/register` | Public | Registers a viewer account |
| POST | `/api/auth/token` | Public | Authenticates credentials and returns a JWT |
| GET | `/api/auth/me` | Authenticated | Returns the current user |
| GET | `/api/users` | Admin | Lists registered users |
| GET | `/api/users/{user_id}` | Admin | Retrieves one user |
| PATCH | `/api/users/{user_id}/role` | Admin | Changes a user's role |
| PATCH | `/api/users/{user_id}/status` | Admin | Activates or disables a user |
| POST | `/api/incidents` | Operator, Admin | Creates an incident |
| GET | `/api/incidents` | Authenticated | Lists incidents with pagination |
| GET | `/api/incidents/{incident_id}` | Authenticated | Retrieves one incident |
| PATCH | `/api/incidents/{incident_id}` | Operator, Admin | Updates an incident |
| DELETE | `/api/incidents/{incident_id}` | Admin | Deletes an incident |
| GET | `/docs` | Public | Opens interactive API documentation |

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
- JWT validation restricts the accepted algorithm and verifies expiration, issuer, and audience.
- The JWT signing secret is stored through private environment configuration.
- Pydantic `SecretStr` reduces accidental secret exposure.
- Login failures use a generic incorrect-credentials response.
- Unknown-email authentication still performs a password-hash verification to reduce timing differences.
- Disabled users cannot log in or continue using previously issued tokens.
- Authorization roles are loaded from the database rather than trusted from token claims.
- Public registration cannot choose an elevated role.
- Administrator endpoints prevent self-demotion and self-deactivation.
- Browser access tokens use session storage instead of persistent local storage.
- Rejected session tokens are removed after `401` or `403` responses.
- Frontend route guards never replace backend authentication or authorization.
- Unsafe external redirect destinations are rejected after login.
- API validation errors are converted into user-readable frontend messages.
- Test credentials and databases are isolated from development data.

Session storage limits token persistence but does not protect a token from malicious JavaScript executing in the same page. Production deployment must maintain strict script controls and avoid unsafe HTML injection.

Rate limiting, refresh tokens, password recovery, email verification, Content Security Policy enforcement, and centralized token revocation remain future production enhancements.

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation and health integration | Complete |
| 2 | PostgreSQL database and backend CRUD API | Complete |
| 3 | Authentication and role-based access control | Complete |
| 4 | Frontend routing and application layout | Complete |
| 5 | Incident management workflow | Planned |
| 6 | Dashboard, filtering, and audit history | Planned |
| 7 | Docker and local service integration | Planned |
| 8 | Automated testing and CI/CD | Planned |
| 9 | Cloud deployment and observability | Planned |

## Author

**AJ C Pipattanakun**

Software Engineering Portfolio Project
