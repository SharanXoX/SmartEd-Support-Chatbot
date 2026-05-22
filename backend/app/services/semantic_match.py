"""Hybrid intent scoring: keywords, fuzzy text, TF-IDF, optional embeddings."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Sequence

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", text.lower()) if len(t) > 2]


def keyword_score(message: str, keywords: Sequence[str]) -> float:
    if not keywords:
        return 0.0
    msg_lower = message.lower()
    msg_tokens = set(tokenize(message))
    parts: list[float] = []
    for kw in keywords:
        k = kw.strip().lower()
        if not k:
            continue
        if k in msg_lower:
            parts.append(1.0)
            continue
        kw_tokens = set(tokenize(k))
        if not kw_tokens:
            continue
        overlap = len(msg_tokens & kw_tokens) / len(kw_tokens)
        parts.append(min(1.0, overlap * 0.95))
    return sum(parts) / len(parts) if parts else 0.0


def fuzzy_score(message: str, search_text: str) -> float:
    if not search_text.strip():
        return 0.0
    if fuzz is not None:
        return float(fuzz.token_set_ratio(message, search_text)) / 100.0
    msg_tokens = set(tokenize(message))
    doc_tokens = set(tokenize(search_text))
    if not doc_tokens:
        return 0.0
    return len(msg_tokens & doc_tokens) / len(doc_tokens)


def cosine_counter(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b[t] for t in a if t in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class TfidfIndex:
    """Lightweight in-memory TF-IDF for support flow documents."""

    def __init__(self) -> None:
        self._doc_vectors: list[Counter[str]] = []
        self._idf: dict[str, float] = {}

    def fit(self, documents: list[str]) -> None:
        n = len(documents)
        if n == 0:
            self._doc_vectors = []
            self._idf = {}
            return
        df: Counter[str] = Counter()
        vectors: list[Counter[str]] = []
        for doc in documents:
            tokens = tokenize(doc)
            c = Counter(tokens)
            vectors.append(c)
            df.update(set(tokens))
        self._idf = {t: math.log((1 + n) / (1 + df[t])) + 1.0 for t in df}
        self._doc_vectors = []
        for c in vectors:
            weighted = Counter({t: c[t] * self._idf.get(t, 1.0) for t in c})
            self._doc_vectors.append(weighted)

    def score_query(self, query: str) -> list[float]:
        q_tokens = tokenize(query)
        q_vec = Counter({t: self._idf.get(t, 1.0) for t in q_tokens})
        return [cosine_counter(q_vec, dv) for dv in self._doc_vectors]


def embedding_cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    sim = dot / (na * nb)
    return max(0.0, min(1.0, (sim + 1) / 2))


def combine_scores(
    *,
    keyword: float,
    fuzzy: float,
    tfidf: float,
    embedding: float,
    w_keyword: float,
    w_fuzzy: float,
    w_tfidf: float,
    w_embedding: float,
) -> float:
    emb = embedding if embedding > 0 else 0.0
    w_emb = w_embedding if emb > 0 else 0.0
    total_w = w_keyword + w_fuzzy + w_tfidf + w_emb
    if total_w <= 0:
        return 0.0
    raw = (
        w_keyword * keyword
        + w_fuzzy * fuzzy
        + w_tfidf * tfidf
        + w_emb * emb
    ) / total_w
    return max(0.0, min(1.0, raw))
