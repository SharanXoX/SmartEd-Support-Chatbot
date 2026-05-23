# Architecture

This document describes how SmartEd Support processes a chat turn and how components communicate. It is intended for engineering teams integrating the copilot into a production LMS.

## Design principle

**The system provides intelligence. The LLM provides language.**

Orchestration validates LMS state, classifies queries, and builds minimal context before any model call.

## High-level components

| Component | Role |
|-----------|------|
| `frontend/` | LMS shell, chat UI, injects `lms_context` per turn |
| `backend/app/routers/` | HTTP/WebSocket boundaries |
| `backend/app/services/response_orchestrator.py` | Navigation vs walkthrough vs conversational |
| `backend/app/services/query_context_resolver.py` | Category, entity match, deterministic outcomes |
| `backend/app/services/lms_context_service.py` | Merge & sanitize active user state |
| `backend/app/services/chat_service.py` | Turn pipeline, LLM invocation |
| `backend/support-assets/` | Indexed walkthrough definitions |
| `mock-data/users/` | Demo student records (replace with LMS API) |

## Request lifecycle (`POST /api/chat/turn`)

```
1. Client sends: message, session_key, current_route, lms_context
2. Rate limit check (per IP)
3. Conversation row loaded/created (session_key)
4. Feature guard — block unsupported LMS features (attendance, payroll, etc.)
5. merge_client_lms_context() — enrich from mock loader / client payload
6. resolve_query_context() — category + entity + optional deterministic reply
7. plan_response() — orchestrator mode (NAVIGATE_ONLY, WALKTHROUGH, CONVERSATIONAL, …)
8. Branch:
   a. Deterministic query resolver reply (entity-specific exams/courses)
   b. Navigation-only response (registry route + user-aware copy)
   c. Bundled visual flow (allowlisted intents, e.g. password_reset)
   d. LLM path — minimal QUERY_SCOPED_CONTEXT + provider JSON completion
9. Persist user/assistant messages + metadata
10. Return ChatTurnResponse (reply, navigation_actions, visual_steps, …)
```

## Frontend ↔ backend communication

- **REST:** `POST /api/chat/turn` with JSON body (`ChatTurnRequest` in `backend/app/schemas.py`).
- **WebSocket:** `/ws/chat/{session_key}` streams text after full turn generation.
- **Demo LMS state:** `GET /api/demo/student?student_id=` for full student snapshot.
- **Proxy:** Vite dev server forwards `/api` and `/health` to port 8000.

### `lms_context` payload (integration contract)

The frontend sends a snapshot of the active learner:

- `student_id`, `current_route`, `courses`, `purchases`, `upcoming_exams`
- `activeUser` object (preferred)
- `available_features`, `available_routes` (registry mirror)

Production: build this object from your LMS APIs instead of `mock-data/`.

## AI inference pipeline

| Stage | LLM used? |
|-------|-----------|
| Intent / route match | No — rules + registry |
| Entity resolution (e.g. “biology exam”) | No |
| Deterministic answers | No |
| Navigation copy | Usually no |
| Walkthrough selection | No — support index |
| General conversation | Yes — scoped prompt only |

Provider selection: `app/ai/provider_factory.py` (`AI_PROVIDER=groq|openai`).

## Chatbot UX modes

| Mode | Behavior |
|------|----------|
| **Navigate only** | `navigation_actions` populated; client auto-routes |
| **Walkthrough** | `visual_steps` + optional hybrid navigation |
| **Conversational** | Text reply; may include citations from RAG |
| **Query resolver** | Fixed reply from validated state (`response_source=query_resolver`) |

## Scaling considerations

- Chat turns are **stateless-friendly** aside from conversation history in DB.
- Horizontal scale: run multiple API replicas behind a load balancer; shared Postgres + Chroma volume.
- Session affinity not required for REST if `session_key` is consistent per browser.
- WebSocket may need sticky sessions or redesign for multi-replica broadcast.
- Move rate limiting to Redis for distributed deployments.

## Future LMS integration

Replace `mock_data_loader.load_student_state()` with HTTP clients:

```
GET /lms/v1/students/{id}/snapshot
→ same shape as mock-data/users/*.json
```

Orchestration layer should remain unchanged if response shapes are stable.

See also: [LMS_COPILOT_ARCHITECTURE.md](./LMS_COPILOT_ARCHITECTURE.md).
