# Production Deployment and Security

Phase 8 provides a hardened container deployment for the Observability &
Incident Detection Platform. The production stack includes PostgreSQL, a
one-time migration service, and the FastAPI application.

## Production Capabilities

The production deployment includes:

- Multi-stage Python container builds
- A dedicated non-root container user
- Read-only container filesystems
- Dropped Linux capabilities
- Disabled privilege escalation
- PostgreSQL health checks
- Ordered database migrations
- Application liveness and readiness checks
- API-key authentication
- Trusted-host validation
- Security response headers
- Per-client fixed-window rate limiting
- Environment-specific configuration validation
- Persistent PostgreSQL storage
- GitHub Actions quality and container validation

## Architecture

The production Compose stack contains three services:

1. `postgres` stores application data in a persistent Docker volume.
2. `migration` applies Alembic migrations and exits successfully.
3. `api` starts only after PostgreSQL is healthy and migrations complete.

The migration and API services use the same production image. This ensures
that the database migration history and application code remain synchronized.

## Prerequisites

Install the following tools on the deployment host:

- Docker Engine or Docker Desktop
- Docker Compose
- Git

Confirm that Docker is available:

```powershell
# Display installed Docker and Compose versions.
docker --version
docker compose version
```

## Production Environment File

Create the real production environment file from the tracked template:

```powershell
# Copy the safe template to an ignored production environment file.
Copy-Item `
  .env.production.example `
  .env.production
```

Edit `.env.production` and replace every placeholder before deployment.

Required sensitive values include:

- `POSTGRES_PASSWORD`
- `OBSERVABILITY_API_KEY`

The production environment file is excluded from Git and must never be
committed.

### Generate Secure Credentials

PowerShell can generate independent random credentials:

```powershell
# Generate a random 48-byte PostgreSQL password encoded as Base64.
$databasePasswordBytes = New-Object byte[] 48
[System.Security.Cryptography.RandomNumberGenerator]::Fill(
  $databasePasswordBytes
)
[Convert]::ToBase64String($databasePasswordBytes)

# Generate a separate random 48-byte API key encoded as Base64.
$apiKeyBytes = New-Object byte[] 48
[System.Security.Cryptography.RandomNumberGenerator]::Fill(
  $apiKeyBytes
)
[Convert]::ToBase64String($apiKeyBytes)
```

Store the generated values in an approved secret manager when deploying
outside a local machine. Do not reuse the database password as the API key.

### Trusted Hosts

`OBSERVABILITY_TRUSTED_HOSTS` must be a JSON list containing every hostname
accepted through the HTTP `Host` header.

Example:

```dotenv
# Allow the public API hostname and the internal Compose service hostname.
OBSERVABILITY_TRUSTED_HOSTS=["api.example.com","api"]
```

Do not use `"*"` in production. Production configuration validation rejects
wildcard trusted hosts.

If a reverse proxy performs health checks with `localhost` or `127.0.0.1`,
include those values explicitly.

## Validate Configuration

Validate environment interpolation before creating containers:

```powershell
# Resolve the complete Compose model using the production environment file.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  config --quiet
```

A successful command produces no output. Validation fails when required
variables are missing or the Compose file is malformed.

To review the resolved model, use:

```powershell
# Inspect the resolved configuration without starting any containers.
# Treat this output as sensitive because it contains resolved credentials.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  config
```

Do not copy resolved configuration output into logs, issues, or pull requests.

## Build the Production Image

Build the application image:

```powershell
# Pull the latest approved base image and build the production application.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  build --pull
```

Confirm that the image uses the dedicated non-root user:

```powershell
# The expected configured user is 10001:10001.
docker image inspect `
  observability-platform:local `
  --format '{{.Config.User}}'
```

Expected result:

```text
10001:10001
```

## Start the Production Stack

Start PostgreSQL, run migrations, and launch the API:

```powershell
# Start services in detached mode.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  up -d
```

Review all service states:

```powershell
# Include the completed one-time migration container in the output.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  ps -a
```

Expected states:

- `postgres`: running and healthy
- `migration`: exited with status code `0`
- `api`: running and healthy

If migration exits with a nonzero status, the API does not start.

## Health Checks

Liveness confirms that the API process is running:

```powershell
# Liveness does not require an API key or database access.
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/health/live" `
  -Method Get
```

Readiness confirms that the application can access PostgreSQL:

```powershell
# Readiness returns HTTP 503 when the database is unavailable.
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/health/ready" `
  -Method Get
```

The legacy endpoints remain available for compatibility:

- `GET /health`
- `GET /health/db`

Health routes remain public so container orchestrators and load balancers can
evaluate the service without storing application credentials.

## Authenticated API Requests

All business endpoints require the `X-API-Key` header in production.

```powershell
# Load the API key from the ignored production environment file or a secret
# manager. Do not place the real credential directly in shell history.
$headers = @{
  "X-API-Key" = $env:OBSERVABILITY_API_KEY
}

# Request a protected business resource.
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/services" `
  -Method Get `
  -Headers $headers
```

Missing or incorrect credentials return HTTP `401`.

## Rate Limiting

Production requires rate limiting to remain enabled.

The following variables control the fixed window:

- `OBSERVABILITY_RATE_LIMIT_REQUESTS`
- `OBSERVABILITY_RATE_LIMIT_WINDOW_SECONDS`

Protected responses include:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

A request exceeding the configured allowance receives HTTP `429` and a
`Retry-After` header.

The current limiter stores counters inside one API process. A multi-instance
deployment should replace it with a shared backend such as Redis so every
instance observes the same client allowance.

## Security Headers

API and health responses include:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy`
- `Cache-Control: no-store`

Production responses also include HTTP Strict Transport Security. TLS should
terminate at a trusted reverse proxy or ingress before public traffic reaches
the application.

## Inspect Container Hardening

Resolve the API container identifier:

```powershell
# Store the exact container ID used by later inspection commands.
$apiContainerId = docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  ps -q api
```

Inspect the security configuration:

```powershell
# Confirm that the root filesystem is read-only.
docker inspect `
  --format '{{.HostConfig.ReadonlyRootfs}}' `
  $apiContainerId

# Confirm that all Linux capabilities were dropped.
docker inspect `
  --format '{{json .HostConfig.CapDrop}}' `
  $apiContainerId

# Confirm that privilege escalation is disabled.
docker inspect `
  --format '{{json .HostConfig.SecurityOpt}}' `
  $apiContainerId
```

Expected values:

```text
true
["ALL"]
["no-new-privileges:true"]
```

## View Logs

Display logs for all production services:

```powershell
# Follow current API, migration, and PostgreSQL output.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  logs --follow
```

Display only API logs:

```powershell
# Follow structured request and application logs from the API.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  logs --follow api
```

Secrets must never be written to application logs.

## Deploy an Application Update

Pull the approved source revision and rebuild:

```powershell
# Download the approved Git revision before rebuilding.
git pull --ff-only

# Rebuild the application using the current production definition.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  build --pull

# Recreate services and apply new migrations before the API starts.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  up -d
```

Verify readiness after every deployment:

```powershell
# Confirm database-backed readiness after the update.
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/health/ready" `
  -Method Get
```

## Database Backup

Create a logical PostgreSQL backup before deployments containing migrations:

```powershell
# Write a timestamped database dump outside the database container.
$backupTimestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "observability-$backupTimestamp.sql"

docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  exec -T postgres `
  pg_dump `
    -U observability `
    -d observability |
  Set-Content `
    -Path $backupPath `
    -Encoding utf8
```

Move backups to encrypted storage with access control and a documented
retention policy. Test restoration procedures regularly.

## Rollback Strategy

Application rollback and database rollback are separate operations.

For an application rollback:

1. Select the previously approved Git revision or container image.
2. Confirm that it is compatible with the current database schema.
3. Rebuild or redeploy that application version.
4. Verify `/health/live` and `/health/ready`.
5. Run focused functional checks.

Do not automatically execute `alembic downgrade` during application rollback.
Schema downgrades can destroy data. Restore a verified database backup when a
migration cannot be reversed safely.

## Stop the Stack

Stop containers while retaining production data:

```powershell
# Remove containers and the network while preserving the database volume.
docker compose `
  --env-file .env.production `
  -f compose.production.yaml `
  down
```

Do not add `--volumes` in production unless permanent database deletion is
explicitly intended and a verified backup exists.

## Continuous Integration

The GitHub Actions workflow validates:

- Python compilation
- A single Alembic migration head
- PostgreSQL migration upgrades
- Missing migration detection
- Ruff linting and formatting
- Complete automated tests
- Production Compose configuration
- Production image builds
- Non-root container execution
- Application imports inside the image
- Migration availability inside the image

The workflow uses read-only repository permissions and cancels obsolete runs
when a newer commit is pushed to the same branch or pull request.