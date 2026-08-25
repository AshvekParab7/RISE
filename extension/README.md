# RISE Focus Guard extension

This is an isolated Chrome Manifest V3 package for the second, browser-enforcement phase of Focus. It does not modify the RISE website or backend.

## Load locally

1. Start the RISE frontend and backend on the same host: either `http://localhost:5173` with `http://localhost:8000`, or the matching `127.0.0.1` pair.
2. Sign in to RISE and open `/focus` once so the extension content script can hand the page JWT to the service worker.
3. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select this `RISE/extension` folder.
4. Start a Focus session with at least one READY resource. While the server reports `ACTIVE`, main-frame HTTP/HTTPS navigation is redirected to `focus-lock.html`.

## Runtime contract

- The content script reads `localStorage.rise_access_token` only on the RISE localhost page and hands it to the service worker through a runtime message.
- The service worker polls `GET /api/study-sessions/focus/current/` every 15 seconds.
- Smart Break uses the existing `POST /api/study-sessions/{id}/focus/smart-break/question/` and `POST /api/study-sessions/{id}/focus/smart-break/answer/` endpoints. The answer key never enters the extension.
- A future `PAUSED_BREAK` with a future `break_unlock_expires_at` removes the blocking rule. The worker polls again to relock after expiry.
- `localhost` and `127.0.0.1` are excluded from the navigation rule so the RISE app and API remain reachable.

## Scope and limitations

This is a development scaffold, not tamper-resistant enforcement. A user can disable or remove the extension, use another browser/profile, use incognito without extension access, close the browser, or go offline. The JWT is held in `chrome.storage.session` and disappears with the browser session. Production use needs a threat model, explicit install/update policy, offline behavior, and a backend session channel designed for extension clients.