# RISE Google OAuth Setup (Phase 3A)

This phase implements only Google Account OAuth foundation. Google Classroom and Google Calendar API calls are intentionally deferred to Phase 3B.

## Official documentation consulted

- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google OAuth 2.0 scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
- [Configure OAuth consent and choose scopes](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Google Identity Services client ID setup](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
- [Google Classroom authorization](https://developers.google.com/workspace/classroom/guides/auth)
- [Google Calendar authorization](https://developers.google.com/workspace/calendar/api/auth)
- [OAuth 2.0 policies](https://developers.google.com/identity/protocols/oauth2/policies)
- [Google API Python client](https://github.com/googleapis/google-api-python-client)

The implementation follows Google's backend web-server authorization-code flow: generate a cryptographically random `state`, redirect to Google, validate the returned state, exchange the one-time code on Django, validate the ID token, then persist the connection server-side.

## 1. Create a Cloud project

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project for RISE development.
3. Keep separate projects for development/staging and production.
4. Do not commit downloaded client credentials.

## 2. Configure the OAuth consent screen

1. Open **Google Auth Platform > Branding**.
2. Set the application name to `RISE`.
3. Add a support email and developer contact email.
4. Configure the audience. For an External testing app, add test users under **Audience**.
5. Add the required homepage/privacy links when preparing a production app.
6. Under **Data Access**, request only:
   - `openid`
   - `profile`
   - `email`

These are the minimum identity/profile scopes for Phase 3A. Classroom and Calendar scopes are intentionally not requested yet. Request future scopes incrementally when those features are implemented.

## 3. Create web credentials

1. Open **Google Auth Platform > Clients**.
2. Create an OAuth client.
3. Choose **Web application**.
4. Add the exact redirect URI:

```text
http://localhost:8000/api/integrations/google/callback/
```

For a deployed environment, use the exact HTTPS backend callback URL. Scheme, host, path, and trailing slash must match exactly.

Authorized JavaScript origins are not needed for this backend-controlled authorization-code flow. If Google Identity Services is added later, configure the frontend origin separately, for example:

```text
http://localhost:5173
```

## 4. Configure environment variables

Copy `.env.example` to `.env` and set:

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google/callback/
GOOGLE_OAUTH_SCOPES=openid profile email
GOOGLE_TOKEN_ENCRYPTION_KEY=...
GOOGLE_SUCCESS_REDIRECT_URI=http://localhost:5173/integrations
```

`GOOGLE_CLIENT_SECRET` must remain backend-only. Never put it in Vite environment variables or browser requests.

`GOOGLE_TOKEN_ENCRYPTION_KEY` should be a Fernet key generated for the deployment. If it is omitted in development, the implementation derives a key from Django's secret key; production deployments should provide a dedicated key through a secret manager.

## 5. Run

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

The authenticated frontend calls:

```text
GET /api/integrations/google/
GET /api/integrations/google/start/
DELETE /api/integrations/google/
```

The callback is:

```text
GET /api/integrations/google/callback/
```

The status response never includes access tokens, refresh tokens, or the client secret.

## Deferred scopes

When Phase 3B begins, request only the scopes required by the specific feature and use incremental authorization:

- Classroom: choose the narrowest applicable `https://www.googleapis.com/auth/classroom.*.readonly` scopes for course/material/assignment reads.
- Calendar: prefer `https://www.googleapis.com/auth/calendar.readonly` for read-only synchronization unless write access is explicitly required.

These scopes are not requested or used in Phase 3A.

## Classroom Phase 3B setup

1. In the same Google Cloud project, enable **Google Classroom API**.
2. Under Google Auth Platform > Data Access, add these read-only scopes when the Classroom sync feature is used:
   - `https://www.googleapis.com/auth/classroom.courses.readonly`
   - `https://www.googleapis.com/auth/classroom.coursework.me.readonly`
   - `https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly`
3. Reauthorize through the RISE Classroom sync action so these scopes are added incrementally.
4. Keep Classroom test users configured while the consent screen is in testing.

The sync service follows Google's paginated list APIs using `nextPageToken`, respects permitted student-visible course/work states, stores stable Google IDs, and maps Google API errors to safe application messages. It does not call Calendar or Classroom write endpoints.

## Calendar Phase 3C setup

1. Enable **Google Calendar API** in the same Cloud project.
2. Reauthorize from RISE when Calendar sync is first used.
3. The Calendar authorization adds only `https://www.googleapis.com/auth/calendar.readonly` incrementally.
4. Select calendars in RISE before syncing; the implementation does not assume `primary` is the only calendar.

Calendar sync covers the initial window of 30 days in the past through 180 days in the future. It stores `nextSyncToken` per selected calendar and performs a full resync after Google's `410 Gone` invalid-token response. Recurring master events are retained with recurrence metadata; event times remain timezone-aware and all-day events are preserved as all-day records.
