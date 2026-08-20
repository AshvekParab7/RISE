# Smart Tutor Django App

This Django app contains the isolated Smart Tutor backend. It handles tutor conversations, PDF-grounded questions, citations, and Markdown-formatted answers.

## Endpoints

- `POST /api/smart-tutor/tutor/`: Ask a tutor question, optionally with a PDF upload.
- `GET /api/smart-tutor/conversations/`: List the authenticated user's tutor conversations.
- `POST /api/smart-tutor/flashcards/`: Generate PDF-grounded topic flashcards. Accepts multipart `topic`, `file`, and optional `count` (default `3`, maximum `20`).
- `POST /api/smart-tutor/mcqs/`: Generate PDF-grounded multiple-choice questions. Accepts multipart `topic`, `file`, and optional `count` (default `4`, maximum `20`).

PDF uploads must be PDF files no larger than 20 MB. Flashcard generation extracts the uploaded PDF text and supplies it as the only reference to the model.

Tutor prompts require valid Markdown output. The frontend renders that Markdown for the user.

## Data and migrations

Tutor conversations and messages are exposed through the `smart_tutor` app models. Their existing database tables retain the historical `ai_` table names so the migration handoff preserves existing data.

Run migrations from the `backend` directory:

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py makemigrations --check --dry-run
```

## Verification

```bash
./.venv/bin/python manage.py check
./.venv/bin/python manage.py test apps.ai
```
