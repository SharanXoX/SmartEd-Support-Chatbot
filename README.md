# SmartEd Support · Visual-first AI Chatbot

Production-grade scaffold for an AI customer-support assistant that blends conversational guidance with **screenshots, overlays, clarifying questions, RAG citations**, and **human escalation**.

To reuse your **master project prompt** in Cursor consistently, paste it into **Cursor Settings → Rules / Instructions**, or save it under `.cursor/rules/` as a dedicated rule file.

## Architecture

```
frontend/      React + Tailwind + Framer Motion widget + admin dashboard
backend/       FastAPI · JWT admin auth · REST + WebSocket · Postgres ORM
ai_engine/     Embeddings + Chroma ingestion utilities (installable package)
vector_db/     Chroma persistence directory (created at runtime)
docker/        Backend Dockerfile + Nginx SPA Dockerfile + nginx.conf
docs/          API notes + deployment guide + schema overview
```

### Highlights

- **Adaptive visual support engine**: Drop folders under `backend/support-assets/` (`metadata.json`, `steps.json`, `stepN.png`) — auto-indexed at startup with hybrid matching (keywords + fuzzy + TF-IDF + optional OpenAI embeddings). New issues need **no code changes**.
- **Groq-first chat**: `AI_PROVIDER=groq` by default; flip to `AI_PROVIDER=openai` without rewriting orchestration.
- **Visual Guidance Engine**: structured `visual_steps[]` with carousel overlays for LLM replies and dedicated walkthrough cards for bundled flows.
- **RAG**: optional OpenAI embeddings + Chroma cosine retrieval over ingested docs (chat still works without embeddings when using Groq-only).
- **Intent + confidence**: flow matcher produces deterministic guided UX; LLM path keeps JSON intents + escalation thresholds.
- **Admin**: uploads KB + screenshots, FAQ CRUD, analytics + conversation summaries.

## Quick start (development)

### One command — API + chat UI (recommended)

From the **repository root**:

```bash
npm install                      # root: installs concurrently
npm install --prefix frontend      # first clone only (React/Vite deps)
npm run dev
```

Then open the chatbot:

- **Chat widget / UI:** [http://localhost:5173](http://localhost:5173)
- **API health:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive API docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

On Windows you can double‑click **`scripts/start-dev.bat`** (runs `npm install` once if needed, then `npm run dev`).

The UI dev server proxies `/api`, `/demo-assets`, `/ws`, and `/health` to `http://localhost:8000`. Ensure Python deps are installed for `backend` (see below).

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install ..\ai_engine
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

For local development, `DATABASE_URL` defaults to **SQLite** (`backend/smarted_support.db`). Set `DATABASE_URL` to a Postgres URL for production-style runs (or use Docker Compose).

Required env vars:

- `GROQ_API_KEY` (defaults to `AI_PROVIDER=groq`)
- `JWT_SECRET`
- Optional `OPENAI_API_KEY` when `AI_PROVIDER=openai`
- Optional `OPENAI_API_KEY` **also** powers embeddings/RAG (Chroma). Chat works without it when you only need Groq + bundled flows.

Optional tuning:

- `INTENT_FLOW_THRESHOLD` (default `0.38`)
- `GROQ_MODEL` (example `llama-3.1-70b-versatile`)

Bootstrap admin (optional):

- `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api`, `/uploads`, `/demo-assets`, `/ws`, `/health` → `http://localhost:8000`.

### Docker Compose

Docker Desktop can show **Engine running** while terminals still report `docker: command not found` (PATH not updated). Use either:

```bash
npm run docker:up
```

or double‑click **`scripts/start-docker.bat`** (prepends Docker’s bin folder on Windows, then `docker compose up --build -d`).

UI on **http://localhost:8080** (Nginx routes `/api`, `/uploads`, `/demo-assets`, `/ws` to the API container).

After code changes, rebuild: `npm run docker:up` (not just restart) so the API image includes new flows/Groq logic.

## Environment template

See `.env.example`.

## Docs

- [`docs/API.md`](docs/API.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/database-schema.md`](docs/database-schema.md)

## Notes / Next iterations

- Wire Alembic migrations for controlled schema rollout.
- Add Redis-backed rate limiting + WS auth if exposing anonymously at scale.
- Harden uploads with MIME sniffing + antivirus scanning.
- Expand ingestion sources (website crawling workers) asynchronously.
