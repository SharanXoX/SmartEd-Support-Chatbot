# SmartEd Support Chatbot

**AI-native LMS copilot** for contextual student support: navigation, course/exam-aware answers, guided walkthroughs, and human escalation — designed for integration into an existing E-learning platform.

| | |
|---|---|
| **Repository** | https://github.com/SharanXoX/SmartEd-Support-Chatbot |
| **Status** | Handoff-ready prototype with production-oriented structure |
| **License** | Internal / assign per your organization |

---

## Overview

SmartEd Support is an **embedded assistant** that sits inside a student LMS. It helps learners:

- Find the right page (exams, courses, certificates, purchases, profile)
- Get answers grounded in **their** enrollments and schedules
- Follow **approved** visual guides (e.g. password reset)
- Escalate to human support when needed

The system uses **deterministic orchestration first** and the **LLM second** (for natural language only). This reduces hallucinated routes, fake courses, and wrong exam dates.

### User interaction flow (simplified)

1. Student opens the LMS and the floating **“Need help?”** chat.
2. Each message sends: question + current page + active student context (courses, exams, etc.).
3. Backend classifies intent, resolves entities (e.g. “biology exam”), validates LMS state.
4. Response may: navigate to a page, return a deterministic answer, run a bundled walkthrough, or call the LLM with **minimal scoped context**.
5. Student sees the reply and optional in-app navigation.

---

## Features

- **AI chatbot support** — Groq (default) or OpenAI via provider abstraction
- **LMS navigation assistance** — registry-driven routes; navigate-only for feature lookups
- **Contextual responses** — query-aware filtering; multi-user demo simulation
- **API integration** — REST chat turn, demo LMS state endpoints, WebSocket streaming
- **Scalable architecture** — stateless-friendly chat turns; modular services
- **Deployment-ready structure** — Docker Compose, Nginx reverse proxy, health checks, logging
- **Admin** — FAQ/KB upload, visual asset library, conversation analytics (JWT-protected)
- **Support flow engine** — drop-in folders under `backend/support-assets/`

---

## Tech stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion |
| **Backend** | FastAPI, SQLAlchemy, Pydantic Settings |
| **AI provider** | Groq (default), OpenAI (optional) |
| **Database** | SQLite (local dev), PostgreSQL (Docker / production) |
| **Vector store** | Chroma (optional RAG / flow index cache) |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## Architecture overview

```
Student LMS (React)
        │
        ▼
Chat widget + session context
        │
        ▼
Backend API  (/api/chat/turn, /api/demo/*, /health)
        │
        ├── AI Orchestration  (intent, entity, navigation, query resolver)
        ├── LMS context merge  (mock JSON today → LMS APIs tomorrow)
        ├── Support flow index  (screenshot walkthroughs)
        └── LLM provider  (Groq / OpenAI — formatting & conversation)
                │
                ▼
        Knowledge: support-assets, FAQs, RAG (optional)
```

Detailed design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · Copilot rules: [`docs/LMS_COPILOT_ARCHITECTURE.md`](docs/LMS_COPILOT_ARCHITECTURE.md)

---

## Folder structure

```
smarted-support/
├── frontend/              # React LMS demo + floating chat
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── routers/       # HTTP routes (chat, admin, demo, auth)
│   │   ├── services/      # Orchestration, AI, LMS context, RAG
│   │   ├── middleware/    # Request logging
│   │   └── ai/            # LLM provider adapters
│   ├── flows/             # Legacy JSON flow definitions
│   ├── support-assets/    # Dynamic walkthrough packs
│   └── tests/             # Unit tests (context, query resolver)
├── mock-data/             # Demo users (alex, sam, priya, john)
├── ai_engine/             # Embeddings + Chroma utilities
├── docker/                # Dockerfiles + Nginx config
├── docs/                  # Architecture, API, deployment
├── scripts/               # Dev / Docker helper scripts
└── .env.example           # Environment template
```

---

## Local development setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- (Optional) Docker Desktop for compose-based runs

### Clone and install

```bash
git clone https://github.com/SharanXoX/SmartEd-Support-Chatbot.git
cd SmartEd-Support-Chatbot
cp .env.example .env
# Edit .env — set GROQ_API_KEY and JWT_SECRET at minimum

npm install
npm install --prefix frontend
```

### Run (recommended — API + UI)

```bash
npm run dev
```

| Service | URL |
|---------|-----|
| LMS demo + chat | http://localhost:5173 |
| API health | http://localhost:8000/health |
| OpenAPI docs | http://localhost:8000/docs |

### Backend only

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate    # Windows
pip install ../ai_engine
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api`, `/health`, `/ws`, and static asset paths to port **8000**.

---

## Environment variables

See [`.env.example`](.env.example). Required for chat:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Primary LLM (when `AI_PROVIDER=groq`) |
| `JWT_SECRET` | Admin API tokens (min 16 chars) |
| `OPENAI_API_KEY` | Optional: OpenAI chat and/or embeddings |

Integration URLs:

| Variable | Purpose |
|----------|---------|
| `BACKEND_URL` | Documented API base for integrators |
| `FRONTEND_URL` | Documented UI origin |
| `PUBLIC_BASE_URL` | Absolute URLs for screenshots in responses |
| `CORS_ORIGINS` | Allowed browser origins |

---

## API endpoints

Summary (full reference: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness — `{"status":"healthy"}` |
| POST | `/api/chat/turn` | Main chat turn |
| GET | `/api/demo/students` | Demo user list |
| GET | `/api/demo/student` | Student state by `student_id` |
| POST | `/api/demo/ticket` | Support ticket escalation |
| POST | `/api/auth/login` | Admin JWT login |
| WS | `/ws/chat/{session_key}` | Streaming assistant reply |

---

## Deployment readiness

- **Environment configs** — `.env.example`, Pydantic settings, Docker Compose
- **Modular design** — orchestration isolated in `backend/app/services/`
- **Health check** — `GET /health` for probes
- **Logging** — HTTP request timing; chat turn latency + response source
- **Docker** — `docker compose up --build` (UI on port 8080)
- **Reverse proxy** — `docker/nginx.conf` routes `/api` and `/ws` to API

See [`docs/DEPLOYMENT_NOTES.md`](docs/DEPLOYMENT_NOTES.md).

---

## Future improvements

- Hardened auth (SSO / LMS JWT → student identity)
- Replace `mock-data/` with live LMS REST APIs
- Redis-backed rate limits and session store
- Observability (OpenTelemetry, structured JSON logs)
- RBAC for admin vs learner surfaces
- Analytics dashboard for conversation quality
- Expanded vector KB ingestion pipelines
- Adaptive learning / proactive nudges (orchestrated, not prompt-only)

---

## Documentation index

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Request lifecycle & AI pipeline |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Endpoints, payloads, auth |
| [docs/DEPLOYMENT_NOTES.md](docs/DEPLOYMENT_NOTES.md) | Ports, Docker, production checklist |
| [docs/LMS_COPILOT_ARCHITECTURE.md](docs/LMS_COPILOT_ARCHITECTURE.md) | Orchestration principles for integrators |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Handoff / PR expectations |
| [docs/GITHUB_BACKUP.md](docs/GITHUB_BACKUP.md) | Clone & push instructions |

---

## Security

- Never commit `.env` or API keys (enforced via `.gitignore`).
- Set `ENABLE_DEBUG_ROUTES=false` in production.
- Rotate `JWT_SECRET` and provider keys per environment.
- Disable `BOOTSTRAP_ADMIN_*` after initial admin creation in production.

---

## Quick test

1. `npm run dev`
2. Open http://localhost:5173/demo/dashboard
3. Settings → switch demo user (Alex / Priya / etc.)
4. Click **Need help?** → ask “When do I have my exams?”

Expected: answers and navigation match the **active** demo user only.
