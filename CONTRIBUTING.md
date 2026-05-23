# Contributing & handoff notes

This repository is structured for integration into an existing E-learning platform.

## Branching

- `main` — stable handoff / deployment baseline
- Use feature branches for integration work (`integrate/lms-api`, `ops/docker`, etc.)

## Before opening a PR

1. Do not commit `.env` files or API keys.
2. Run `npm run build` in `frontend/`.
3. Run backend tests: `cd backend && python -m pytest tests/ -q`
4. Verify `GET /health` returns `{"status":"healthy",...}`.

## Code areas

| Path | Responsibility |
|------|----------------|
| `frontend/` | React LMS demo shell + embedded chat widget |
| `backend/app/services/` | AI orchestration, query resolution, LMS context |
| `backend/support-assets/` | Screenshot walkthrough packs (metadata + steps) |
| `mock-data/users/` | Demo student JSON (replace with LMS API later) |
| `docs/` | Architecture, API, deployment |

## Integration team

See `docs/LMS_COPILOT_ARCHITECTURE.md` for orchestration principles and `docs/DEPLOYMENT_NOTES.md` for ports and environment assumptions.
