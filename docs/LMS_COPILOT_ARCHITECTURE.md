# LMS AI Copilot — Master Architecture

Continuation guide for extending and hardening the SmartEd LMS Copilot. **Do not redesign from scratch.**

## Project goal

AI-native LMS Copilot embedded in an e-learning platform.

**The assistant IS:**

- LMS navigation helper
- Contextual, session-aware support
- Workflow guide (approved flows only)
- Active-user-state-only answers

**The assistant IS NOT:**

- Generic ChatGPT wrapper
- Free-form chatbot
- Autonomous route-deciding AI
- Unrestricted reasoning engine

## Core principle

**The SYSTEM provides intelligence. The LLM provides language.**

Never rely on: giant prompts, full LMS dumps, conversation memory, unrestricted LLM reasoning.

Always rely on: orchestration, deterministic routing, structured state, validated context, query-aware filtering, feature registry, session-aware data access.

## Architecture flows

**Current:**

```
Frontend → Mock JSON → Orchestration → LLM
```

**Target:**

```
Frontend → FastAPI → LMS APIs / Database → Orchestration → LLM
```

**Target request pipeline:**

```
Student → Frontend Chatbot → AI Orchestrator API
  → Session validation → Intent detection → Entity resolution
  → LMS APIs / DB → Context sanitization → Minimal prompt → LLM
  → Frontend action response (nav / text)
```

## Non-negotiable backend rule

The LLM must **never** interact with LMS state blindly.

Before any data reaches the LLM, the backend MUST:

1. Fetch  
2. Validate  
3. Sanitize  
4. Structure  
5. Scope  

## Stack

| Layer | Tech |
|--------|------|
| Frontend | React, TypeScript, Tailwind, Framer Motion, Vite, React Router |
| Backend | FastAPI |
| AI | Groq (now), OpenAI (later), provider abstraction |
| Deploy | Docker Compose |

## Domain model (portable)

Mock LMS mirrors production: students, courses, exams, certifications, purchases, announcements, calendar, profile, settings, support/help.

Orchestration must survive mock → real API transition with **minimal rewrites** (same shapes, different data source).

## Implementation roadmap

### Step 1 — Standardize data shapes

Use production-like structures everywhere. Example:

```json
{
  "studentId": "priya-001",
  "name": "Priya",
  "courses": [
    { "id": "bio101", "title": "Introduction to Biology", "progress": 100, "completed": true }
  ],
  "exams": [
    { "id": "exam1", "courseId": "bio101", "scheduledAt": "2026-06-10", "status": "scheduled" }
  ]
}
```

Avoid ad-hoc flags (`{ "bio": true, "examA": "soon" }`).

### Step 2 — Data access layer

Never scatter `mockUsers[id]` reads. Use services:

- Today: `studentService.getCourses(userId)` → mock JSON  
- Later: same method → `GET /api/student/courses`

### Step 3 — Backend endpoints (production-shaped)

Expose early, mock-backed:

- `GET /student/:id/courses`
- `GET /student/:id/exams`
- `GET /student/:id/certifications`
- `GET /student/:id/purchases`

Swap implementation to real LMS later without changing orchestration contracts.

### Step 4 — Orchestration lives in backend

| Backend | Frontend |
|---------|----------|
| Intent, entity, route validation, permissions, sanitization, feature validation, query-aware fetch, minimal prompts, action routing | Render UI, navigate, display responses |

### Step 5 — Session identity

**Now:** active demo user id (browser storage).  
**Later:** JWT → `student_id` → fetch **only** that student's state.

### Step 6 — Query-aware fetching

Do not load full profile every turn.

| Query type | Fetch scope |
|------------|-------------|
| Exam | Active exams, related incomplete courses |
| Course | Active courses, progress |
| Certification | Certificates, completed courses |
| Purchase | Purchases only |

### Step 7 — Real LMS integration (phased)

1. Real auth, mock courses/exams  
2. Real courses API  
3. Real exams + purchases  
4. Full production state under orchestration  

## AI orchestration layer (not “AI inside LMS”)

Backend = **AI Gateway**: aggregation, orchestration, validation, retrieval, permissions, action routing, prompt building, deterministic navigation.

LLM = explain, format, converse — **only** from scoped context.

## Query-aware context

| Category | Inject | Exclude |
|----------|--------|---------|
| Exam | Active exams, related active courses | Completed/certified courses, unrelated purchases |
| Certification | Certificates, completed courses | Active exam noise |
| Purchase | Purchases | Unrelated enrollments |
| Course | Active progress, next modules | Archived unless asked |

## AI safety

**Never hallucinate:** routes, features, exams, workflows, screenshots, permissions.

**LMS feature registry** = single source of truth (`lms_feature_registry.py`, `lmsRegistry.ts`).

## Screenshot policy

Only **`password_reset`** may use visual walkthroughs. Everything else: navigation-only or concise text.

## UX philosophy

Calm, contextual, deterministic, LMS-native, production-safe — not verbose, generic, or chatty.

## Existing modules (preserve & extend)

| Module | Role |
|--------|------|
| `query_context_resolver.py` | Category, entity, deterministic outcomes, minimal prompts |
| `context_sanitizer.py` | Active vs completed filtering |
| `lms_context_service.py` | Merge client context, build scoped prompts |
| `response_orchestrator.py` | Navigation vs walkthrough vs conversational |
| `feature_first_routing.py` | Registry-first navigation |
| `navigation_registry.py` | Allowed routes/keywords |
| `mock_data_loader.py` | User state from `mock-data/users/` |
| `ActiveUserContext` / `ChatContext` | Session + per-turn `lms_context` |

## Long-term maturity

1. Real database integration  
2. Better entity resolution  
3. Retrieval layer  
4. Analytics & telemetry  
5. Auth hardening  
6. Concurrency testing  
7. Cost optimization  
8. Provider failover  
9. Streaming orchestration  
10. Tool execution layer  

## When changing code

- **Do not** rebuild UI or replace orchestration unnecessarily.  
- **Do not** add full student dumps to LLM prompts.  
- **Do** extend data access layer and keep shapes stable.  
- **Do** add deterministic rules before LLM fallback.  
- **Do** test with multiple mock users (Alex, Sam, Priya, John + new profiles).
