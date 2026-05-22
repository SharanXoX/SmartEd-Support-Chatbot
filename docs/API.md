## SmartEd Support API (FastAPI)

Base URL (Docker Compose behind Nginx): `http://localhost:8080`

Public endpoints:

| Method | Path | Notes |
|-------:|------|------|
| GET | `/health` | Liveness |
| POST | `/api/chat/turn` | Stateless-friendly chat turn |
| WS | `/ws/chat/{session_key}` | Streams assistant reply chunks after generation |

Authentication:

| Method | Path | Notes |
|-------:|------|------|
| POST | `/api/auth/login` | JSON `{email,password}` → JWT |
| POST | `/api/auth/token` | OAuth2 password form (`username` is email) |
| POST | `/api/auth/bootstrap-first-admin` | Allowed only when **zero** users exist |

Admin (`Authorization: Bearer <jwt>`):

| Method | Path | Notes |
|-------:|------|------|
| GET | `/api/admin/analytics/summary` | Conversations/messages/tickets/FAQ/KB counts |
| GET | `/api/admin/faqs` | List FAQs |
| POST | `/api/admin/faqs` | Create FAQ |
| DELETE | `/api/admin/faqs/{id}` | Delete FAQ |
| POST | `/api/admin/knowledge/upload` | Multipart file ingestion → Chroma |
| DELETE | `/api/admin/knowledge/{id}` | Delete asset + vectors |
| POST | `/api/admin/visuals/upload` | Multipart screenshot library (`title`,`tags`,`file`) |
| GET | `/api/admin/visuals` | List visuals |
| GET | `/api/admin/conversations` | Recent conversations |
| GET | `/api/admin/conversations/{id}/messages` | Conversation transcript |

Static assets:

| Method | Path | Notes |
|-------:|------|------|
| GET | `/uploads/visuals/{filename}` | Tutorial screenshots uploaded via admin |
| GET | `/demo-assets/{path}` | Bundled screenshots for JSON-defined support flows |

Rate limiting:

- Global SlowAPI defaults apply (`RATE_LIMIT_DEFAULT`, default `60/minute`).
- `/api/chat/turn` adds `45/minute` per IP.

Schemas align with `backend/app/schemas.py`. Chat payloads additionally expose:

- `response_source`: `"support_flow"` (matched JSON flow) or `"llm"`
- `matched_flow_intent`, `intent_match_confidence` when a bundled flow triggers
