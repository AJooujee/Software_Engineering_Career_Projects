# Phase 9 Production Release Evidence

## Release Summary

| Item | Result |
|---|---|
| Status | Production deployment and validation complete |
| Release date | 2026-09-08 |
| Source revision | `32ba84f1d310410fda315c9e348acc8fb0ab87d3` |
| Azure region | `northcentralus` |
| Resource group | `rg-cloud-operations-portfolio-northcentralus` |
| Public application | [Cloud Operations Platform](https://frontend-bdo5hkkvipb3s.victoriousforest-190ae510.northcentralus.azurecontainerapps.io) |
| Deployment name | `phase9-ncus-release-20260908050608` |

The production release uses immutable backend and frontend GHCR images tagged with the source revision. Azure provider validation passed, and a fresh ARM what-if predicted nine creates and zero deletes before explicit deployment authorization.

## Production Resource Inventory

| Azure resource | Name | Purpose |
|---|---|---|
| Log Analytics workspace | `log-cloudops-portfolio-bdo5hkkvipb3s` | Central application, system, and PostgreSQL diagnostic logs |
| PostgreSQL Flexible Server | `pg-cloudops-portfolio-bdo5hkkvipb3s` | Persistent production data |
| Container Apps environment | `cae-cloudops-portfolio-bdo5hkkvipb3s` | Consumption hosting and log integration |
| Container Apps Job | `migration-bdo5hkkvipb3s` | Explicit one-shot Alembic migrations |
| Backend Container App | `backend-bdo5hkkvipb3s` | Internal FastAPI API |
| Frontend Container App | `frontend-bdo5hkkvipb3s` | Public HTTPS Nginx and React entry point |

All primary resources reported a successful provisioning state. The migration execution `migration-bdo5hkkvipb3s-ncyjiz7` subsequently completed with `Succeeded`, and the idempotent administrator bootstrap completed successfully. No administrator email, password, token, connection string, or subscription identifier is recorded in this document.

## Production Smoke Evidence

| Check | Result |
|---|---|
| Direct backend liveness | Healthy |
| Direct backend readiness | Database available |
| Nginx proxy liveness | Healthy |
| Nginx proxy readiness | Database available |
| Request correlation | One safe `X-Request-ID` per response |
| SPA fallback | HTTP 200 |
| Fingerprinted JavaScript asset | HTTP 200 |
| Security headers | Present with restrictive frontend CSP |
| Asset caching | `public, immutable, max-age=31536000` |
| Required API paths | Present |
| Authenticated administrator workspace | Verified in the production UI |

## Observability Evidence

The Log Analytics workspace was provisioned with 30-day retention and a 1 GB daily ingestion cap. The compact validation window completed through `2026-09-08T18:30:37Z`.

### Application Console Logs

| App | Records | Structured requests | Error-like records |
|---|---:|---:|---:|
| `backend-bdo5hkkvipb3s` | 407 | 192 | 0 |
| `frontend-bdo5hkkvipb3s` | 410 | 0 | 0 |

The frontend is an Nginx workload, so its access output is not expected to use the FastAPI structured-request schema.

### Azure System Logs

| App | Records | Errors | Warnings |
|---|---:|---:|---:|
| `backend-bdo5hkkvipb3s` | 55 | 0 | 10 |
| `frontend-bdo5hkkvipb3s` | 59 | 0 | 11 |

The warning records were consistent with expected Container Apps lifecycle behavior, including cold-start readiness and scale-to-zero activity. There were no Azure system errors for either application.

## Cost Boundary

| Control | Configuration |
|---|---|
| Container Apps | Consumption plan, minimum replicas 0, maximum replicas 1 |
| PostgreSQL | `Standard_B1ms`, 32 GB storage, high availability disabled |
| PostgreSQL backups | Seven-day retention, geo-redundancy disabled |
| Log Analytics | 30-day retention, 1 GB daily cap |
| Network | No customer-managed VNet in the cost-first profile |
| Azure budget | Monthly monitoring with 50%, 80%, and 100% email alerts |

Budget alerts notify; they do not suspend or delete resources. PostgreSQL remains the principal continuously provisioned service even when both Container Apps scale to zero.

## Security and Release Boundary

- Only the frontend has public Container Apps ingress.
- The backend uses internal Container Apps ingress.
- PostgreSQL requires TLS and credentials.
- The cost-first public database endpoint is restricted by its firewall configuration but is not equivalent to private networking.
- Runtime secrets are supplied during deployment and are not committed.
- The release consumes immutable commit-SHA images.
- Infrastructure deployment, migration, and administrator bootstrap are separate approval steps.
- Structured request logs exclude query-string values.
- Repository documentation excludes deployment secrets, credentials, administrator identity, and the Azure subscription identifier.

This file is safe release evidence, not a secret backup or a substitute for Azure resource state.
