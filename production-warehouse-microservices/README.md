# Production Warehouse Microservices

A production-oriented warehouse and inventory management backend built with Python, FastAPI, PostgreSQL, Docker, automated testing, and CI/CD.

## Planned Services

| Service | Port | Responsibility |
|---|---:|---|
| API Gateway | 8000 | Routes requests to backend services |
| Inventory Service | 8001 | Products, inventory levels, and stock movements |
| Warehouse Service | 8002 | Warehouses and stock transfers |
| Order Service | 8003 | Orders and inventory reservations |

## Current Progress

- [x] Project architecture initialized
- [x] Inventory Service FastAPI application
- [x] Health-check endpoint
- [x] Automated health-check test
- [ ] Product and inventory APIs
- [ ] PostgreSQL integration
- [ ] Warehouse Service
- [ ] Order Service
- [ ] API Gateway
- [ ] Docker Compose
- [ ] GitHub Actions CI/CD

## Inventory Service

Run from `services/inventory-service`:

```powershell
python -m uvicorn app.main:app --reload --port 8001