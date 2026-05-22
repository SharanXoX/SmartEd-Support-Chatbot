## Deployment Guide

### Prerequisites

- Docker + Docker Compose
- OpenAI API key with access to chat + embeddings models

### Configure environment

Copy `.env.example` → `.env` and set:

- `OPENAI_API_KEY`
- `JWT_SECRET` (long random string)

Optional:

- `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`
- `ESCALATION_WEBHOOK_URL`

### Run

```bash
docker compose up --build
```

Open:

- UI + reverse proxy: `http://localhost:8080`
- Postgres (optional host access): `localhost:5432`

### Production notes

- Put TLS termination on Nginx or an upstream load balancer (HTTPS-ready architecture).
- Rotate JWT secrets and disable `/api/auth/bootstrap-first-admin` unless locked behind infra ACLs.
- Back up Postgres volume (`pgdata`) and vector persistence volume (`chroma_data`).
- Set `VITE_API_URL` during frontend builds when UI and API are on different origins.
