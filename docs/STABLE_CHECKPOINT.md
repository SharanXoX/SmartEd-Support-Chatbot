# Stable checkpoint — LOCKED WORKING BASELINE

**Status:** Production-like stable baseline for mock LMS + AI support testing.  
**Rule:** Preserve current behavior. Future work must be incremental, isolated, and backwards compatible.

---

## What is frozen (do not change without explicit approval)

- React mock LMS UI (dark theme, sidebar, course cards, floating chatbot)
- All `/demo/*` routes and legacy demo routes
- AI orchestration (`response_orchestrator`, `query_classifier`, `navigation_registry`)
- Navigate-only vs walkthrough vs hybrid vs conversational modes
- `support-assets/` folder structure and discovery/indexing
- Chatbot integration (`ChatContext`, `FloatingChat`, `SupportFlow`)
- Provider modular architecture (Groq/OpenAI)
- Docker setup and dependency versions

---

## Expected chatbot behavior (must remain)

| User intent | System behavior |
|-------------|-----------------|
| Navigation (“open exams”, “show certificates”, “change profile”) | Navigate only → target `/demo/*` page, **no** screenshot walkthrough |
| Workflow / how-to / troubleshooting | Guided walkthrough when a bundled flow matches |
| Conversational / informational | Normal AI reply, no forced navigation |

Examples:

- “Open exams” → `/demo/exams`
- “Show my certificates” → `/demo/certifications` (+ completion note when applicable)
- “Change profile” → `/demo/profile`
- “How do I submit an assignment?” → support flow with screenshots (when matched)

---

## Mock LMS routes (stable)

| Path | Page |
|------|------|
| `/demo/dashboard` | Default landing |
| `/demo/announcements` | Announcements placeholder |
| `/demo/courses` | My Courses |
| `/demo/calendar` | Calendar |
| `/demo/exams` | Exams |
| `/demo/certifications` | Certifications (100% completion) |
| `/demo/purchases` | My Purchases |
| `/demo/profile` | Profile |
| `/demo/settings` | Settings |
| `/demo/help` | Help |

Legacy (preserved for flows): `/demo/assignments`, `/demo/assignment-upload`, `/demo/quizzes`, `/demo/course/:id`, `/demo/policy/:id`. Redirects: `/demo/notes` → courses, `/demo/progress` → profile, `/demo/certificates` → certifications.

Sidebar order: Dashboard → Announcements → My Courses → Calendar → Exams → Certifications → My Purchases → Profile → Settings → Help.

---

## Run tomorrow (same as today)

From repo root:

```powershell
npm run dev
```

- **UI:** http://localhost:5173 (or next free port if 5173 is busy)
- **API:** `npm run dev:api` targets port **8000**; Vite proxy in `frontend/vite.config.ts` forwards to **8001**

If chat navigation or turns fail after reboot, a stale process may be holding a port:

```powershell
scripts\restart-api.ps1
```

Then restart `npm run dev` and hard-refresh the browser (Ctrl+F5).

Docker (unchanged):

```powershell
npm run docker:up
```

Chat UI via Docker: http://localhost:8080

---

## Smoke checklist (no regressions)

1. Frontend loads; sidebar shows all 10 items.
2. Dashboard shows welcome + “See My Courses”.
3. Floating chat opens; quick actions work.
4. “Open exams” → navigates to `/demo/exams` without step cards.
5. “Show my certificates” → `/demo/certifications`.
6. “How do I submit an assignment?” → walkthrough with `visual_steps` when flow matches.
7. Help → “Contact Support” opens ticket modal via chat context.

---

## Key files (reference only — do not refactor)

| Area | Path |
|------|------|
| Routes | `frontend/src/App.tsx` |
| Nav data | `frontend/src/data/mockLms.ts` |
| Layout | `frontend/src/layouts/LmsDemoLayout.tsx` |
| Chat | `frontend/src/context/ChatContext.tsx` |
| Orchestrator | `backend/app/services/response_orchestrator.py` |
| Navigation registry | `backend/app/services/navigation_registry.py` |
| Route context | `backend/app/services/route_context.py` |
| Chat turn | `backend/app/services/chat_service.py` |
| Support flows | `backend/support-assets/` |

---

## Mock data engine (state-driven LMS)

- Data: `mock-data/` (students, courses catalog, announcements)
- API: `GET /api/demo/student?student_id=`, `GET /api/demo/lms-state`, `GET /api/demo/students`
- Frontend: `services/mockApi/`, `context/LmsStateContext.tsx`, `registry/lmsRegistry.ts`
- Chat turns include `lms_context` snapshot (route, courses, exams, available routes/features)
- Unavailable features (attendance, hostel, etc.) blocked by `feature_guard.py` — no fake navigation
- **Screenshot allowlist:** only `password_reset` may return pictorial walkthroughs (`visual_workflow_allowlist.py`)

## Change policy

**Allowed:** small bugfixes, copy tweaks, new `support-assets` topics, env keys, docs, mock-data JSON edits.  
**Not allowed without review:** UI redesign, routing rewrites, orchestrator refactors, dependency upgrades, chatbot behavior changes, removing demo pages.

This document is the stability contract for the checkpoint. See also `docs/WORKING_STATE.md` for day-to-day ops.
