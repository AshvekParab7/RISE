# Adaptive timetable feature

## Folder structure

- `PlannerPage.jsx` is the adaptive `/planner` route. It loads the overview, renders Exam Mission, weak-topic, resource, Deadline Rescue, next-action, and plan-preview panels, and owns upload/confirmation state.
- `CurrentPlannerPage.jsx` is the existing persisted timetable page. It keeps day/week views, manual event create/edit/delete, dark mode, and the RISE planner chat.
- `adaptivePlannerService.js` contains the API calls for overview, next action, plan preview/commit, and exam schedule upload/review.
- `timetable.css` styles the adaptive shell and responsive panels.
- `planner.css` contains the existing detailed timetable styles.

## Flow

1. The page loads `/api/adaptive-planner/overview/` and the owned subjects list. The overview combines exams, college classes, Google Calendar events, study blocks, topics, resources, and Classroom tasks.
2. The timetable source list marks college classes, exams, and Google Calendar events as read-only. Existing RISE study blocks remain editable in the detailed timetable below.
3. Weak topics are ranked by the backend intelligence engine. Each result includes mastery, difficulty, priority reasons, and up to three recommended notes or resources. Files open through the existing authenticated media URL convention.
4. Exam schedules are uploaded as PDF or image files. When configured, the backend sends the original document to Gemini for complete extraction; if that is unavailable, PDFs use backend text extraction and images use browser/server OCR fallbacks. The review step remains editable so the user can verify the title, subject, date, time, and venue before confirmation creates imported exam records.
5. Generate adaptive plan requests a preview. The backend places blocks only in open windows after college classes, Google Calendar events, and existing study blocks. Confirming the preview commits the blocks as normal RISE `PlannerEvent` records.
6. What should I do now? asks the existing intelligence priority engine for the highest-impact topic or subject, including its persisted IDs. Start focus carries that recommendation to the focus screen, where starting the timer creates an ACTIVE StudySession for the selected subject/topic and duration. Returning to focus resumes an existing active session; completing or abandoning it updates the stored session.
7. Deadline Rescue shows incomplete tasks created by Google Classroom sync and links each task back to Classroom when that link is available. Sync uses the existing Classroom integration.

## API surface

- `GET /api/adaptive-planner/overview/`
- `GET /api/adaptive-planner/next-action/`
- `POST /api/adaptive-planner/plan/preview/`
- `POST /api/adaptive-planner/plan/commit/`
- `POST /api/adaptive-planner/exam-schedule-uploads/`
- `GET /api/adaptive-planner/exam-schedule-uploads/<id>/`
- `POST /api/adaptive-planner/exam-schedule-uploads/<id>/confirm/`

## Run and verify

Use Bun from the `frontend` directory:

- `bun install`
- `bun run dev`
- `bun run lint`
- `bun run build`
