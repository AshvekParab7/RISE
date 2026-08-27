# Focus backend module

This module owns Focus-only API behavior while `StudySession` remains in `apps.tasks` for backward compatibility with generic study-session CRUD callers.

## Current integration

- `FocusSessionActionsMixin` is composed into `apps.tasks.views.StudySessionViewSet`, so the existing `/api/study-sessions/` route also exposes `/focus/current/`, `/focus/start/`, and `/{id}/focus/state/`.
- Smart Break is available at `/{id}/focus/smart-break/question/` and `/{id}/focus/smart-break/answer/`; the generated answer key remains server-side.
- `serializers.py` validates authenticated subject, topic, resource ownership, and `READY` processing status.
- `services.py` owns the 45-minute server timer and state synchronization.
- `tests.py` contains the Focus API regression tests.

## Future integration

Add exam, completion quiz, and award transitions here as named actions and service functions. Keep the generic session serializer and CRUD behavior in `apps.tasks` unchanged. A future extension or native client should consume these server-owned transitions rather than maintaining an independent timer or assuming a website can block unrelated browser tabs.