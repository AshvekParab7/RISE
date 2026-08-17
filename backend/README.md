# RISE Backend Phase 1

Django 6 + Django REST Framework foundation for RISE core academic data. This phase intentionally excludes Google integrations, AI/RAG, browser blocking, and advanced planner intelligence.

## Setup

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set PostgreSQL credentials in `.env` before running with PostgreSQL. Development falls back to a local SQLite file only when `DATABASE_NAME` is unset, which keeps checks and tests runnable on a clean machine. Production settings require PostgreSQL environment variables.

## Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
python manage.py test
```

Demo credentials after `seed_demo`:

- Email: `student@rise.local`
- Password: `RiseDemo123!`

## API

- `GET /api/health/`
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET/PATCH /api/auth/me/`
- `/api/semesters/`
- `/api/subjects/`
- `/api/topics/`
- `/api/syllabus/`
- `/api/exams/`
- `/api/college-timetable/`
- `/api/resources/`
- `/api/tasks/`
- `/api/study-sessions/`
- `/api/schema/`
- `/api/docs/`

All resource, academic, task, and study-session querysets are scoped to the authenticated user. File uploads use local `media/` storage with a 20 MB size limit and supported academic document/image extensions.
