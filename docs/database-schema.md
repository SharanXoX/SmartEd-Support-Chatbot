## Database schema (PostgreSQL)

Tables are defined in SQLAlchemy (`backend/app/models.py`). Logical entities:

| Table | Purpose |
|------|---------|
| `users` | Admin accounts (JWT subject is email) |
| `conversations` | Anonymous/`session_key` scoped chats |
| `messages` | Chat transcript (`meta` stores structured assistant payloads) |
| `faqs` | FAQ rows surfaced to the model |
| `knowledge_assets` | Uploaded KB files + stable `source_tag` for vector deletes |
| `visual_guides` | Screenshot library surfaced to the model |
| `support_tickets` | Escalations + transcript snapshots |

Suggested indexes exist on commonly queried columns (`session_key`, foreign keys).

For migrations beyond auto-create, add Alembic in a follow-up (schema starts via `Base.metadata.create_all` at startup).
