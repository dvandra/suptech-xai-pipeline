"""Build and cache embeddings + sparse term stats for the RAG corpus."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

import config
from pipeline.embeddings import get_embedder
from rag.load_corpus import load_documents

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _bm25_stats(docs: list[dict]) -> dict[str, Any]:
    tokenized = [tokenize(d["search_text"]) for d in docs]
    df: Counter = Counter()
    for toks in tokenized:
        df.update(set(toks))
    avgdl = sum(len(t) for t in tokenized) / max(len(tokenized), 1)
    return {
        "tokenized": tokenized,
        "df": dict(df),
        "avgdl": avgdl,
        "n_docs": len(docs),
    }


def bm25_scores(
    query: str, stats: dict[str, Any], k1: float = 1.5, b: float = 0.75
) -> np.ndarray:
    q_toks = tokenize(query)
    n = stats["n_docs"]
    avgdl = stats["avgdl"]
    df = stats["df"]
    scores = np.zeros(n, dtype=np.float32)
    for i, doc_toks in enumerate(stats["tokenized"]):
        tf = Counter(doc_toks)
        dl = len(doc_toks) or 1
        s = 0.0
        for t in q_toks:
            if t not in tf:
                continue
            n_q = df.get(t, 0)
            idf = math.log(1 + (n - n_q + 0.5) / (n_q + 0.5))
            freq = tf[t]
            s += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / avgdl))
        scores[i] = s
    return scores


def build_index(force: bool = False) -> dict[str, Any]:
    config.ensure_dirs()
    meta_path = config.RAG_INDEX_DIR / "meta.json"
    emb_path = config.RAG_INDEX_DIR / "embeddings.npy"

    docs = load_documents()
    if not force and meta_path.exists() and emb_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("doc_ids") == [d["id"] for d in docs]:
            embeddings = np.load(emb_path)
            stats = _bm25_stats(docs)
            return {
                "docs": docs,
                "embeddings": embeddings,
                "embedder_name": meta.get("embedder_name", "cached"),
                "bm25": stats,
            }

    embedder = get_embedder()
    embeddings = embedder.encode([d["search_text"] for d in docs])
    np.save(emb_path, embeddings)
    meta_path.write_text(
        json.dumps(
            {
                "doc_ids": [d["id"] for d in docs],
                "embedder_name": embedder.name,
                "n": len(docs),
            },
            indent=2,
        )
    )
    return {
        "docs": docs,
        "embeddings": embeddings,
        "embedder_name": embedder.name,
        "bm25": _bm25_stats(docs),
    }


def cosine_scores(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    q = query_vec.astype(np.float32)
    qn = np.linalg.norm(q)
    if qn > 0:
        q = q / qn
    # rows assumed L2-normalised by embedder; still guard
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    m = matrix / norms
    return (m @ q).astype(np.float32)
