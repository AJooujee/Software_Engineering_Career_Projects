# Phase 9 Azure Infrastructure

This directory contains the cost-first Azure deployment foundation for the Cloud Operations Platform. The portfolio profile is deployed and validated in Azure North Central US.

## Deployed Portfolio Environment

| Item | Value |
|---|---|
| Region | `northcentralus` |
| Resource group | `rg-cloud-operations-portfolio-northcentralus` |
| Release source | `32ba84f1d310410fda315c9e348acc8fb0ab87d3` |
| Public frontend | [Cloud Operations Platform](https://frontend-bdo5hkkvipb3s.victoriousforest-190ae510.northcentralus.azurecontainerapps.io) |
| Container Apps environment | `cae-cloudops-portfolio-bdo5hkkvipb3s` |
| Frontend app | `frontend-bdo5hkkvipb3s` |
| Backend app | `backend-bdo5hkkvipb3s` |
| Migration job | `migration-bdo5hkkvipb3s` |
| PostgreSQL server | `pg-cloudops-portfolio-bdo5hkkvipb3s` |
| Log Analytics workspace | `log-cloudops-portfolio-bdo5hkkvipb3s` |

Availability is best-effort because this is a cost-controlled portfolio deployment.

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

## Validation and Release Procedure

Compile without deploying resources:

```powershell
az bicep build --file infra/main.bicep --stdout | Out-Null
az bicep build-params --file infra/parameters/portfolio.bicepparam --stdout | Out-Null
```

Before every deployment, confirm the active Azure subscription, verify immutable GHCR commit-SHA images, run ARM provider validation, and review an ARM `what-if`. Do not deploy unless the expected resource changes contain no unplanned deletes.

Infrastructure deployment does not execute migrations or create an administrator. Start the migration job separately, require a `Succeeded` execution, and then run the idempotent administrator bootstrap inside the backend container. Never put a password or deployment secret in shell history, logs, screenshots, or Git.

## Post-deployment Validation

The production release must pass:

- Direct backend liveness and database readiness
- Nginx-proxied liveness and readiness
- One safe request ID per response
- SPA fallback and fingerprinted JavaScript delivery
- Restrictive security headers and immutable asset caching
- Required API route discovery
- Authenticated administrator UI access
- Structured backend request logs in Log Analytics
- Zero unexpected application and Azure system errors

The initial production release passed all checks. Its observation window contained 192 structured backend requests, zero application error-like records, and zero Azure system errors for both applications.

## Cost Operations

The Azure budget and its email alerts monitor spend but do not stop resources. Container Apps can scale to zero, while PostgreSQL remains provisioned until explicitly stopped or deleted. Review Cost Management regularly and remove the resource group when the public portfolio environment is no longer needed.

Do not delete the resource group merely to rerun validation. Teardown is a separate destructive operation and requires an explicit resource inventory and confirmation.
