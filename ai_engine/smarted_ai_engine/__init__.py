"""SmartEd AI engine: embeddings, Chroma persistence, document ingestion."""

from smarted_ai_engine.chroma_store import ChromaKnowledgeStore
from smarted_ai_engine.ingestion import ingest_text_chunks

__all__ = ["ChromaKnowledgeStore", "ingest_text_chunks"]
