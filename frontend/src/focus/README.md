# Focus module

This folder contains the website-only Focus workflow and its API boundary.

## Current integration

- `ClayFocus.jsx` is mounted by the existing `/focus` route in `RISEProduct.jsx`.
- `focusSessionService.js` owns Focus-specific calls under `/study-sessions/focus/*`.
- Smart Break uses the same service boundary for note-grounded questions, server grading, and the ten-minute break authorization countdown.
- `focus.css` contains styles introduced by the Focus module. Shared clay tokens remain in `../clay.css`.
- The backend keeps `StudySession` in `apps.tasks` for compatibility with existing generic session consumers. Focus-only serializers, timing logic, actions, and tests live in `backend/apps/focus`.

## Future integration

Keep new Focus behavior behind `focusSessionService.js` and add backend actions under `apps.focus` rather than placing raw requests in page components. The Chrome extension or native client phase should use the same server-owned session state and should not assume the website can block unrelated browser tabs.

To integrate this module into another frontend, mount `ClayFocus` with `active` and `setActive` props, import `focus.css`, and provide the existing API authentication setup. To integrate another backend route, include `apps.focus` in `INSTALLED_APPS` and reuse the Focus action mixin on the session viewset.