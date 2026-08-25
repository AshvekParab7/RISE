# Adaptive planner backend

## Structure

- `models.py` stores `ExamScheduleUpload` and editable `ExamScheduleRow` records. Existing academic `Exam` and task/planner models remain the sources of truth.
- `serializers.py` validates owned subjects, exam row dates/times, upload requests, and plan requests.
- `views.py` exposes the authenticated API for overview, next action, plan preview/commit, and exam upload/review/confirmation.
- `services/exam_schedule_parser.py` extracts PDF text or image OCR, normalizes candidate rows, and transactionally confirms rows into imported `Exam` records.
- `services/overview.py` assembles missions, weak topics, resources, timetable sources, and Classroom deadlines.
- `services/plan_builder.py` distributes focused blocks around blocked college/calendar/study windows and rechecks conflicts before persistence.

## Data flow

1. A student uploads a PDF or image to `exam-schedule-uploads/`.
2. When `GEMINI_API_KEY` is configured, the backend sends the original PDF or image to Gemini and converts its structured response into all candidate rows. If Gemini is unavailable, the parser uses `pypdf` for selectable PDF text, browser OCR text from the frontend, or Pillow and optional `pytesseract` OCR on the server. Unreadable documents or missing OCR support create a `NEEDS_REVIEW` placeholder row with a clear message.
3. The frontend edits and submits every row. The confirmation service verifies row ownership, subject ownership, time ordering, and semester consistency, then creates or updates an `Exam` with `source=IMPORTED`.
4. Overview generation calls the existing intelligence context and priority engine. Mission progress is derived from topic mastery and exam proximity. Resources are selected per subject, preferring AI-ready material.
5. Plan preview uses those priorities and the existing blocked-window context. It includes college timetable entries, Google Calendar events, existing RISE blocks, and urgent incomplete tasks. Commit revalidates all blocks inside a transaction and writes normal `PlannerEvent` rows.
6. Classroom assignments are read from synced `Task` rows with `source=GOOGLE_CLASSROOM`; the linked `GoogleCoursework` record supplies the Classroom URL.

## Security and validation

All views require authentication. Uploads, rows, subjects, semesters, resources, tasks, exams, and planner events are scoped to the request user. Plan commit rechecks subjects and time conflicts, so a changed or tampered preview cannot bypass another user's data or a blocked timetable window.

## Exam schedule extraction setup

Set `GEMINI_API_KEY` in the backend `.env` to enable multimodal extraction. `GEMINI_MODEL` is optional and defaults to `gemini-3.6-flash`; older unavailable model settings automatically retry with that model. `pytesseract` is declared in `requirements.txt`, but Windows also needs the Tesseract OCR executable installed and available on `PATH` for the local OCR fallback. No extracted row is committed without explicit confirmation.

## API surface

- `GET /api/adaptive-planner/overview/`
- `GET /api/adaptive-planner/next-action/`
- `POST /api/adaptive-planner/plan/preview/`
- `POST /api/adaptive-planner/plan/commit/`
- `POST /api/adaptive-planner/exam-schedule-uploads/`
- `GET /api/adaptive-planner/exam-schedule-uploads/<uuid>/`
- `POST /api/adaptive-planner/exam-schedule-uploads/<uuid>/confirm/`

Run migrations with `python manage.py migrate`, then verify with `python manage.py check` and `python manage.py test apps.adaptive_planner`.
