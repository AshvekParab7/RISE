# RISE Run Guide

RISE has a Django REST API backend and a React/Vite frontend.

## Prerequisites

- Python 3.13 or later
- Node.js and npm
- PowerShell on Windows

The repository already contains a local SQLite database at `backend/db.sqlite3`. PostgreSQL is optional for development when the backend environment is configured to use SQLite.

## Backend

Open a PowerShell terminal at the repository root and run:

```powershell
cd backend
..\..\.venv\Scripts\python.exe manage.py check
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver
```

The API runs at `http://127.0.0.1:8000/`.

Useful backend commands:

```powershell
..\..\.venv\Scripts\python.exe manage.py test
..\..\.venv\Scripts\python.exe manage.py seed_demo
..\..\.venv\Scripts\python.exe manage.py createsuperuser
```

If the virtual environment does not exist, create it and install the backend dependencies:

```powershell
cd backend
py -3.13 -m venv ..\..\.venv
..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Frontend

Open a second PowerShell terminal at the repository root and run:

```powershell
cd frontend
npm install
npm run dev
```

Vite prints the local frontend URL, normally `http://localhost:5173/`.

The frontend uses `frontend/.env`. Set `VITE_API_URL=http://localhost:8000/api` to connect it to the local backend. Firebase and Google values can remain empty unless those integrations are being used.

## Verification

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

Backend checks:

```powershell
cd backend
..\..\.venv\Scripts\python.exe manage.py check
..\..\.venv\Scripts\python.exe manage.py test
```

## Main URLs

- Frontend: `http://localhost:5173/`
- API health check: `http://127.0.0.1:8000/api/health/`
- Django admin: `http://127.0.0.1:8000/admin/`
- API docs: `http://127.0.0.1:8000/api/docs/`

Stop either development server with `Ctrl+C`.
