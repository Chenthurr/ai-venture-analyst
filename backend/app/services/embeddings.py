"""
Embedding generation + hybrid (dense + keyword) retrieval.

Dense retrieval: OpenAI embeddings, cosine similarity computed in-process
with numpy. This avoids requiring a separate vector DB (Qdrant) for the
first working slice -- swap `similarity_search` for a Qdrant-backed
implementation later without changing the callers.

Sparse retrieval: a lightweight BM25-style keyword overlap score, combined
with the dense score (hybrid search), which is what the product spec asks for.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Tuple

import numpy as np
from openai import OpenAI

from app.config import settings


def get_openai_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file to enable AI analysis."
        )
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    client = get_openai_client()
    # OpenAI embeddings API accepts batches; chunk to stay under request limits.
    batch_size = 96
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=settings.openai_embedding_model, input=batch)
        all_embeddings.extend([d.embedding for d in resp.data])
    return all_embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


def bm25_score(query_tokens: List[str], doc_tokens: List[str], avg_doc_len: float,
                k1: float = 1.5, b: float = 0.75) -> float:
    """Simplified single-document BM25 term-frequency score (no corpus IDF term,
    since retrieval here re-ranks within one project's chunks rather than a
    global corpus)."""
    doc_len = len(doc_tokens) or 1
    counts = Counter(doc_tokens)
    score = 0.0
    for term in query_tokens:
        f = counts.get(term, 0)
        if f == 0:
            continue
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * (doc_len / avg_doc_len))
        score += numerator / denominator
    return score


def hybrid_search(
    query: str,
    chunks: List[dict],
    top_k: int = 8,
    dense_weight: float = 0.65,
) -> List[Tuple[dict, float]]:
    """
    chunks: list of {"content": str, "embedding": List[float], ...metadata}
    Returns top_k chunks with a combined score, highest first.
    """
    if not chunks:
        return []

    query_embedding = embed_texts([query])[0]
    query_tokens = _tokenize(query)
    doc_token_lists = [_tokenize(c["content"]) for c in chunks]
    avg_len = sum(len(t) for t in doc_token_lists) / max(len(doc_token_lists), 1) or 1

    scored = []
    for chunk, tokens in zip(chunks, doc_token_lists):
        dense = cosine_similarity(query_embedding, chunk["embedding"]) if chunk.get("embedding") else 0.0
        sparse = bm25_score(query_tokens, tokens, avg_len)
        # Normalize sparse into a roughly 0..1 range for blending
        sparse_norm = sparse / (sparse + 3.0)
        combined = dense_weight * dense + (1 - dense_weight) * sparse_norm
        scored.append((chunk, combined))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
