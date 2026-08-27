# RISE frontend

RISE (Real-time Intelligent Study Engine) is a frontend-only React prototype built with Vite, Tailwind CSS, React Router, Lucide React, Recharts, and Framer Motion.

## Run

```bash
npm install
npm run dev
```

## Verify

```bash
npm run lint
npm run build
```

Mock data and the async service boundary live in `src/data/mockData.js` and `src/services/mockServices.js`. Replace those service implementations with Django REST calls later without changing the page UI contracts. The prototype includes login, six-step onboarding, dashboard, subjects, tasks, notes, planner, focus, tutor, tests, analytics, integrations, and settings routes.

![alt text](image.png)
