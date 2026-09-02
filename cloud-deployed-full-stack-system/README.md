# Cloud Operations Platform

A cloud-ready full-stack application for monitoring services, managing operational incidents, and displaying system health through a single user interface.

This project demonstrates end-to-end software engineering using a React frontend, FastAPI backend, automated testing, environment-based configuration, and a production frontend build.

## Current Status

**Phase 1 — Project Foundation: Complete**

The React frontend can communicate with the FastAPI backend and display the live API health status.

## Current Features

- React single-page frontend
- FastAPI REST API
- Live frontend-to-backend health check
- Local CORS configuration
- Interactive Swagger API documentation
- Automated backend health test
- Reproducible Python and Node dependencies
- Production-ready frontend build command

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
- Pytest
- HTTPX2

### Planned Infrastructure

- PostgreSQL
- Docker and Docker Compose
- GitHub Actions
- Cloud deployment
- Application monitoring

## Project Structure

```text
cloud-deployed-full-stack-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   │   └── test_health.py
│   └── requirements.txt
├── docs/
│   └── architecture.md
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── .env.example
├── .gitignore
└── README.md
```

## Local Development

The backend and frontend run in separate terminals during local development.

### 1. Start the Backend

From the project directory:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 2. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```text
http://127.0.0.1:5173
```

## Automated Testing

Run the backend tests from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result:

```text
tests/test_health.py::test_health_check PASSED
```

## Production Frontend Build

Run from the `frontend` directory:

```powershell
npm run build
```

Vite generates the optimized production files inside `frontend/dist`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Confirms that the backend API is running |
| GET | `/health` | Returns the backend service health status |
| GET | `/docs` | Opens the interactive Swagger documentation |

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation and health integration | Complete |
| 2 | PostgreSQL database and backend CRUD API | Planned |
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