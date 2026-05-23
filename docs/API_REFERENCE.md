# API Reference

Base URL (local dev): `http://localhost:8000`  
Base URL (Docker Compose + Nginx): `http://localhost:8080`

Interactive docs: `/docs` (Swagger UI)

---

## Operations

### `GET /health`

Liveness probe.

**Response 200**

```json
{
  "status": "healthy",
  "service": "SmartEd Support API"
}
```

---

## Chat (public)

### `POST /api/chat/turn`

Primary endpoint for the embedded widget.

**Rate limit:** 45/minute per IP (plus global default).

**Request body**

```json
{
  "session_key": "abc123def456",
  "message": "When do I have my exams?",
  "current_route": "/demo/dashboard",
  "lms_context": {
    "student_id": "priya-001",
    "current_route": "/demo/dashboard",
    "activeUser": {
      "id": "priya-001",
      "name": "Priya",
      "courses": [],
      "upcomingExams": []
    },
    "available_features": ["dashboard", "courses", "exams"],
    "available_routes": {
      "exams": "/demo/exams"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_key` | string | yes | 8–64 chars; browser session id |
| `message` | string | yes | User message |
| `current_route` | string | no | LMS path for route-aware replies |
| `lms_context` | object | no | Active learner snapshot |

**Response 200** (`ChatTurnResponse`)

```json
{
  "reply": "Your upcoming exams:\n• **Data Science Final** — June 18, 2026 · 9:00 AM",
  "intent": "exam_query",
  "confidence": 0.92,
  "visual_steps": [],
  "navigation_actions": [
    { "label": "Open Exams", "path": "/demo/exams" }
  ],
  "suggested_replies": ["View exams", "My courses", "Contact support"],
  "escalate": false,
  "response_source": "query_resolver",
  "response_type": "query_resolver",
  "response_mode": "conversational"
}
```

Common `response_source` values: `navigation`, `support_flow`, `llm`, `query_resolver`, `fallback`.

---

## Demo LMS (mock integration)

Used by the React demo; replace with your LMS in production.

### `GET /api/demo/students`

**Response**

```json
{
  "students": [
    { "id": "alex-001", "name": "Alex", "profile_type": "beginner" }
  ]
}
```

### `GET /api/demo/student?student_id=priya-001`

Returns full mock student state (courses, exams, certificates, purchases, …).

### `GET /api/demo/lms-state?student_id=&current_route=`

Aggregated state + `available_features` / `available_routes` registry.

### `POST /api/demo/ticket`

Create support escalation ticket.

**Request**

```json
{
  "name": "Priya",
  "email": "priya@example.com",
  "issue": "Payment failed on checkout",
  "session_key": "abc123"
}
```

---

## Authentication (admin)

### `POST /api/auth/login`

```json
{ "email": "admin@example.com", "password": "secret" }
```

**Response**

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Subsequent admin routes: `Authorization: Bearer <jwt>`.

### `POST /api/auth/token`

OAuth2 password form (`username` = email).

### `POST /api/auth/bootstrap-first-admin`

Allowed only when zero users exist in database.

---

## Admin (JWT required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/analytics/summary` | Usage counts |
| GET/POST/DELETE | `/api/admin/faqs` | FAQ CRUD |
| POST | `/api/admin/knowledge/upload` | KB file → Chroma |
| POST | `/api/admin/visuals/upload` | Screenshot library |
| GET | `/api/admin/conversations` | Recent sessions |
| GET | `/api/admin/conversations/{id}/messages` | Transcript |

---

## WebSocket

### `WS /ws/chat/{session_key}`

Client sends JSON text frames; server streams assistant reply after generation. Same business logic as REST turn (see `ws_chat` router).

---

## Static assets

| Path | Content |
|------|---------|
| `/uploads/visuals/` | Admin-uploaded images |
| `/demo-assets/` | Legacy demo screenshots |
| `/support-assets/` | Walkthrough step images |

---

## Error responses

| Code | Meaning |
|------|---------|
| 400 | Validation error |
| 401 | Invalid/missing JWT (admin) |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Server error (check logs) |

---

## Auth expectations for integrators

| Surface | Auth |
|---------|------|
| Chat turn | Public (rate-limited); trust `lms_context` from your LMS backend in production |
| Demo endpoints | Public in dev; **disable or protect** in production |
| Admin | JWT required |
| Debug (`/debug/*`) | Disable via `ENABLE_DEBUG_ROUTES=false` |

Production recommendation: issue `lms_context` from your backend after validating the student session; do not let the browser forge enrollments.
