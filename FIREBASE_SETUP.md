# Firebase Google Login Setup

## Firebase project

1. Create or select a Firebase project.
2. Add a Web App in Project settings.
3. Open Authentication, then Sign-in method.
4. Enable the Google provider.
5. Add `localhost` to Authentication authorized domains.

## Frontend configuration

Copy the Web App configuration into `frontend/.env.local`:

```dotenv
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
```

These values are used only by the Firebase Web SDK. Do not commit `frontend/.env.local`.

## Django Admin configuration

Create a Firebase service account from Project settings > Service accounts. Put its values in `backend/.env`:

```dotenv
FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

The backend also supports a service-account JSON path:

```dotenv
FIREBASE_SERVICE_ACCOUNT_JSON=
```

Never commit the service-account JSON or private key. The backend verifies Firebase ID tokens and issues the existing RISE JWT access and refresh tokens.

## Run locally

Restart both processes after changing environment variables:

```powershell
cd backend
python manage.py migrate
python manage.py runserver
```

```powershell
cd frontend
npm run dev
```

Google Login uses Firebase only for identity. Google Classroom and Google Calendar continue using the existing backend-controlled OAuth connections.
