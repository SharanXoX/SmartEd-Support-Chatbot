"""Quick local test for adaptive support indexer."""

from app.config import get_settings
from app.services.support_indexer import get_support_indexer

settings = get_settings()
idx = get_support_indexer()
n = idx.refresh(settings, force=True)
print("indexed", n)
for q in ["I forgot my password", "I can't access my account", "payment declined"]:
    m = idx.match(settings, q)
    print(q, "->", m.flow.intent if m else None, round(m.confidence, 3) if m else None, m.scores if m else None)
