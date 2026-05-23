# Deployment Notes

Guidance for platform teams deploying SmartEd Support alongside an E-learning product.

## Environment setup

1. Copy `.env.example` → `.env` (repo root; loaded by backend bootstrap).
2. Set required secrets:
   - `GROQ_API_KEY` (or `OPENAI_API_KEY` with `AI_PROVIDER=openai`)
   - `JWT_SECRET` (long random string, ≥16 characters)
3. Set `DATABASE_URL` to PostgreSQL in production.
4. Set `CORS_ORIGINS` to your LMS UI origin(s).
5. Set `PUBLIC_BASE_URL` to the browser-facing URL (for absolute screenshot links).
6. Set `ENABLE_DEBUG_ROUTES=false`.
7. Set `MOCK_STUDENT_ENABLED=false` when real LMS APIs supply context.

Optional integration documentation vars (not read by all code paths today):

- `BACKEND_URL` — document your deployed API URL for integrators
- `FRONTEND_URL` — document your LMS/chat host

## Ports (default)

| Service | Port | Notes |
|---------|------|-------|
| Vite dev (frontend) | 5173 | `npm run dev` |
| Uvicorn API | 8000 | `uvicorn app.main:app` |
| Docker Nginx UI | 8080 | `docker compose up` |
| PostgreSQL | 5432 | Compose service `db` |

## Health checks

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"SmartEd Support API"}
```

Configure load balancer probes on `/health` (HTTP 200).

## Docker deployment

```bash
docker compose up --build -d
```

- UI + reverse proxy: http://localhost:8080  
- API reachable at http://localhost:8080/api/... (proxied)  
- Rebuild images after backend/frontend changes: `docker compose up --build`

Windows helper: `scripts/start-docker.bat`  
Dev helper: `scripts/start-dev.bat`

## Reverse proxy readiness

`docker/nginx.conf` terminates HTTP and forwards:

- `/api` → FastAPI
- `/ws` → WebSocket
- `/health` → health check
- `/` → static React build

For production TLS, place HTTPS termination at Nginx or an upstream load balancer (ALB, Ingress, etc.).

## Deployment assumptions

| Topic | Assumption |
|-------|------------|
| **Identity** | Demo uses client-side user switcher; production should pass verified `student_id` in `lms_context` |
| **Data** | `mock-data/` is for QA; replace with LMS APIs |
| **Secrets** | Provided via environment, not baked into images |
| **Storage** | Persistent volumes for Postgres, Chroma, uploads |
| **Admin** | Bootstrap admin only on first run; disable public bootstrap in prod |

## Production checklist

- [ ] `JWT_SECRET` rotated; bootstrap admin password changed
- [ ] `ENABLE_DEBUG_ROUTES=false`
- [ ] `MOCK_STUDENT_ENABLED=false` (when LMS integrated)
- [ ] CORS restricted to known origins
- [ ] Rate limits reviewed (`RATE_LIMIT_DEFAULT`)
- [ ] Postgres backups configured
- [ ] Log aggregation attached (stdout JSON recommended)
- [ ] `/health` monitored
- [ ] Provider API keys in secret manager (not plain `.env` on disk)

## Logging

- HTTP: `smarted.http` — method, path, status, duration (ms)
- Chat: `smarted.chat` — session prefix, route, response mode/source, latency
- Startup: provider env status, support flow index count

## Frontend production build

```bash
cd frontend
# Optional when API is on another host:
# set VITE_API_URL=https://api.yourdomain.com
npm run build
```

Serve `frontend/dist` via Nginx or CDN. Docker image builds this automatically.

## Next step: full container hardening

1. Multi-stage images (already under `docker/`)
2. Non-root container user
3. Secret injection via K8s secrets / AWS SSM
4. Separate staging/prod compose overlays
5. CI pipeline: lint → test → build → push image

See also [DEPLOYMENT.md](./DEPLOYMENT.md) (legacy) and root [README.md](../README.md).
