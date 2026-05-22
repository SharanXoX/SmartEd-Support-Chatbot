"""Retrieve context passages from Chroma + ingest uploads."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from smarted_ai_engine.chroma_store import ChromaKnowledgeStore
from smarted_ai_engine.ingestion import ingest_text_chunks, load_document_text

from app.config import Settings


@lru_cache
def _store(api_key: str, persist_dir: str, collection: str, embedding_model: str) -> ChromaKnowledgeStore:
    return ChromaKnowledgeStore(
        persist_directory=persist_dir,
        collection_name=collection,
        openai_api_key=api_key,
        embedding_model=embedding_model,
    )


def get_store(settings: Settings) -> ChromaKnowledgeStore | None:
    if not settings.openai_api_key:
        return None
    return _store(
        settings.openai_api_key,
        settings.chroma_persist_dir,
        settings.chroma_collection,
        settings.embedding_model,
    )


def retrieve_context(settings: Settings, query: str, k: int = 6) -> list[dict]:
    store = get_store(settings)
    if store is None:
        return []
    return store.query(query, k=k)


def ingest_document(settings: Settings, *, path: Path, source_tag: str) -> int:
    """Returns number of chunks written."""

    store = get_store(settings)
    if store is None:
        raise RuntimeError("OpenAI API key missing; cannot embed documents.")
    text = load_document_text(path)
    chunks, metas = ingest_text_chunks(text)
    if not chunks:
        return 0
    store.delete_source(source_tag)
    store.upsert_chunks(texts=chunks, metadatas=metas, source=source_tag)
    return len(chunks)
