# SmartEd Support — working state (saved reference)

> **Master architecture (Cursor continuation):** [`LMS_COPILOT_ARCHITECTURE.md`](./LMS_COPILOT_ARCHITECTURE.md) · rule: `.cursor/rules/lms-copilot-architecture.mdc`

> **Stable checkpoint:** See [`STABLE_CHECKPOINT.md`](./STABLE_CHECKPOINT.md) — project is locked as a production-like baseline. Do not refactor architecture or change chatbot navigation behavior without explicit approval.

Last verified: mock LMS (10 sidebar sections), route-aware **navigate-only** AI, workflow screenshots when needed, Groq follow-ups, Docker path.

## Mock E-Learning demo (local)

```powershell
npm run dev
```

Open **http://localhost:5173** — student portal demo (Alex), 10-item sidebar, and floating support chat.

- Mock student context: `backend/mock_student.json`
- Demo routes: dashboard, announcements, courses, calendar, exams, certifications, purchases, profile, settings, help (+ legacy assignments/quizzes/course detail)
- Navigation-only phrases: “open exams”, “show certificates”, “edit profile”, “open settings” (no screenshot walkthrough)
- Workflow flows: `enroll_course`, `submit_assignment`, `watch_lecture`, `view_grades`, `download_notes`, etc. under `backend/support-assets/`
- Tickets: say “I need human help”, Help page **Contact Support**, or quick action
- Policy FAQs seed on first API start (refund / grading / attendance)

**Ports:** `npm run dev:api` uses **8000**; `frontend/vite.config.ts` proxies API to **8001**. If API calls fail after restart, run `scripts\restart-api.ps1` and ensure only one API listener matches the Vite proxy port.

## Quick start

```powershell
# From repo root (Docker Desktop running)
scripts\start-docker.bat
# or
npm run docker:up
```

**Chat UI:** http://localhost:8080  
**API health:** http://localhost:8080/health  
**Support catalog:** http://localhost:8080/debug/support-catalog  
**Example image:** http://localhost:8080/support-assets/password_reset/step1.png  

## Environment (`.env` at repo root)

- `GROQ_API_KEY` — required for open-ended / follow-up AI (not for bundled walkthroughs)
- `GROQ_MODEL=llama-3.3-70b-versatile` (do not use decommissioned `llama3-70b-8192`)
- `PUBLIC_BASE_URL` — leave **empty** for `npm run dev` (port 5173). Docker sets `http://localhost:8080` automatically.
- `AI_PROVIDER=groq`

## Add new support topics (no code changes)

1. Create folder: `backend/support-assets/<issue_id>/`
2. Add `metadata.json`, optional `steps.json`, and `step1.png`, `step2.png`, …
3. Restart API or `POST /api/admin/support/reindex` (admin auth)

See `backend/support-assets/README.md`.

## Architecture highlights

| Piece | Location |
|--------|----------|
| Dynamic indexer | `backend/app/services/support_indexer.py` |
| Image URLs + disk check | `backend/app/services/asset_urls.py` |
| Hybrid match (keyword + fuzzy + TF-IDF) | `backend/app/services/semantic_match.py` |
| Chat orchestration | `backend/app/services/chat_service.py` |
| Screenshot UI | `frontend/src/components/ImageCard.tsx`, `SupportFlow.tsx` |

## Local dev (no Docker)

```powershell
npm run dev
```

UI: http://localhost:5173 (proxies API + `/support-assets`)

## Visual walkthrough (screenshot cards)

Bundled flows return structured JSON (not plain text only):

- `response_type`: `"support_flow"`
- `reply`: short intro only (step text lives in `visual_steps`)
- `visual_steps[]`: `{ step, title, description, image_url }` with paths like `/support-assets/password_reset/step1.png`

The UI renders `SupportFlow` when `response_type` / `response_source` is `support_flow` and `visual_steps` is non-empty (`ChatMessage.tsx`).

**If you only see text and no screenshots:**

1. Stop all dev servers (`Ctrl+C` on `npm run dev` terminals).
2. Run `scripts\restart-api.ps1` (or kill stale Python on port 8000).
3. Start again: `npm run dev` → open **http://localhost:5173** and hard refresh (Ctrl+F5).

A stale API process on port 8000 can serve an old payload (long `reply` with steps inlined, missing `response_type`).

## Troubleshooting

- **`docker` not found`** — use `scripts\start-docker.bat` or add Docker’s bin to PATH
- **Images not showing** — use port **5173** for dev (not 8080 without Docker); hard refresh (Ctrl+F5)
- **After replacing PNGs** — restart API (`npm run dev`); check file sizes updated in `support-assets/`
- **Plain text only / no step cards** — restart API with `scripts\restart-api.ps1`; confirm `POST /api/chat/turn` returns `response_type: support_flow` and `visual_steps`

For future updates, continue from this doc and the main `README.md`.
