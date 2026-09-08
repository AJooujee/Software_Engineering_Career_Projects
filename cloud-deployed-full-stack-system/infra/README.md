# Phase 9 Azure Infrastructure

This directory contains the cost-first Azure deployment foundation for the Cloud Operations Platform.

## Topology

- Azure Container Apps consumption environment without a customer-managed VNet
- External Nginx frontend Container App
- Internal FastAPI backend Container App reached through environment service discovery
- Manual Container Apps migration job running `alembic upgrade head`
- Azure Database for PostgreSQL Flexible Server 18 using `Standard_B1ms`
- 32 GB PostgreSQL storage, seven-day backup retention, no high availability, and no geo-redundant backup
- Log Analytics with 30-day retention and a 1 GB daily ingestion cap
- PostgreSQL server logs exported to a resource-specific Log Analytics table

## Cost and Security Boundary

The portfolio profile intentionally avoids custom Container Apps VNet integration because that topology adds billed load-balancer and public-IP resources. PostgreSQL therefore uses a public endpoint with mandatory TLS, a strong generated credential, and an Azure-services firewall rule.

The Azure-services rule permits network attempts from Azure-assigned addresses outside this subscription. PostgreSQL authentication and TLS still apply. A production or paid environment should replace this profile with private networking and managed database identity.

## Secret Handling

`portfolio.bicepparam` reads deployment-only values from these process environment variables:

- `PHASE9_BACKEND_IMAGE`
- `PHASE9_FRONTEND_IMAGE`
- `PHASE9_POSTGRES_ADMIN_PASSWORD`
- `PHASE9_JWT_SECRET_KEY`

Never commit their values. The image variables should use immutable GHCR commit-SHA tags. The PostgreSQL password must be URL-safe because the application receives it inside a SQLAlchemy connection URL.

## Runtime and Observability Contract

The backend keeps `/health` as a dependency-free liveness endpoint and exposes `/health/ready` for database-backed readiness. Container Apps and Compose use readiness for traffic eligibility while liveness can distinguish a running process from a usable application.

Every HTTP response carries one `X-Request-ID`. Nginx creates the edge identifier, forwards it to FastAPI, suppresses the duplicate upstream header, and returns the same identifier to the caller. FastAPI emits compact JSON request events containing only the identifier, method, path, status code, duration, and sanitized exception type. Query strings, request bodies, credentials, tokens, and client IP addresses are deliberately excluded.

The frontend image renders `nginx.conf` from an environment-variable template. `BACKEND_UPSTREAM` is `backend:8000` in Compose and the internal backend Container App name in Azure. `NGINX_ENVSUBST_FILTER` restricts substitution so Nginx runtime variables remain intact.

The frontend responses add a restrictive Content Security Policy and Permissions Policy while retaining the existing clickjacking, MIME-sniffing, and referrer protections.

## Validation

Compile without deploying resources:

```powershell
az bicep build --file infra/main.bicep --stdout | Out-Null
az bicep build-params --file infra/parameters/portfolio.bicepparam --stdout | Out-Null
```

Run an Azure Resource Manager `what-if` before every deployment. Do not run a deployment until the expected resource list and current subscription have been reviewed.
