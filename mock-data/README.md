# Mock LMS data engine

Simulated multi-user LMS state for SmartEd support testing. The API loads these JSON files; the frontend mirrors them via `/api/demo/student` and injects `activeUser` into every chat turn.

## Layout

- `users/` — per-learner snapshots (`alex.json`, `sam.json`, `priya.json`, `john.json`, `index.json`)
- `students/` — legacy snapshots (used only if `users/` index is missing)
- `courses/catalog.json` — shared course catalog metadata
- `announcements/default.json` — shared announcements merged when a user has none

## Demo users

| ID | File | Profile |
|----|------|---------|
| alex-001 | alex.json | Beginner, 2 courses, exams, no certificates |
| sam-001 | sam.json | Overdue, 1 purchase/course, low progress |
| priya-001 | priya.json | Advanced, completed courses, certificates, premium purchases |
| john-001 | john.json | New user, empty enrollments (onboarding) |

Switch the active learner in **Settings** or **Profile → Switch Demo User** (browser `localStorage` + per-user chat session in `sessionStorage`).

## AI safety

Only routes in `AVAILABLE_LMS_ROUTES` may be used for navigation. The assistant must answer from the **active user** context only — never another learner's enrollments or purchases. Requests for unsupported features (attendance, hostel, payroll, etc.) are refused by `feature_guard.py`.
