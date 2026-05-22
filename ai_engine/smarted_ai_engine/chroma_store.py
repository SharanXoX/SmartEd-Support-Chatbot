"""ChromaDB-backed semantic store with OpenAI embeddings."""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

import chromadb
from chromadb.config import Settings
from openai import OpenAI


def _chunk_id(source: str, chunk_index: int, text: str) -> str:
    raw = f"{source}:{chunk_index}:{text[:200]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class ChromaKnowledgeStore:
    """Thin wrapper around Chroma persistent client + OpenAI embeddings."""

    def __init__(
        self,
        *,
        persist_directory: str,
        collection_name: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._oa = OpenAI(api_key=openai_api_key)
        self._embedding_model = embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._oa.embeddings.create(model=self._embedding_model, input=texts)
        return [item.embedding for item in resp.data]

    def upsert_chunks(
        self,
        *,
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
        source: str,
    ) -> None:
        ids: list[str] = []
        embeddings = self.embed(list(texts))
        for i, text in enumerate(texts):
            ids.append(_chunk_id(source, i, text))
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=list(texts),
            metadatas=[
                {**m, "source": source} for m in metadatas
            ],
        )

    def query(self, query: str, k: int = 6) -> list[dict[str, Any]]:
        q_emb = self.embed([query])[0]
        res = self._collection.query(
            query_embeddings=[q_emb],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict[str, Any]] = []
        if not res["documents"] or not res["documents"][0]:
            return hits
        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
            strict=False,
        ):
            hits.append({"content": doc, "metadata": meta or {}, "distance": float(dist)})
        return hits

    def delete_source(self, source: str) -> None:
        """Remove all chunks tagged with metadata source == source."""
        self._collection.delete(where={"source": source})
