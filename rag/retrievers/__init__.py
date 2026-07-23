"""Retriever implementations for Stage 6 RAG exploration."""
from __future__ import annotations

from typing import Any

import numpy as np

import config
from pipeline.embeddings import get_embedder
from rag.index import bm25_scores, build_index, cosine_scores


def _topk(scores: np.ndarray, docs: list[dict], k: int) -> list[dict]:
    order = np.argsort(-scores)
    out = []
    for i in order[:k]:
        if scores[i] <= 0 and len(out) > 0:
            # still allow zeros for tiny corpora
            pass
        d = dict(docs[int(i)])
        d["score"] = float(scores[int(i)])
        out.append(d)
    return out[:k]


_EMBEDDER = None


def _embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = get_embedder()
    return _EMBEDDER


def retrieve_dense(query: str, index: dict | None = None, k: int | None = None) -> list[dict]:
    index = index or build_index()
    k = k or config.RAG_TOP_K
    embedder = _embedder()
    q = embedder.encode([query])[0]
    scores = cosine_scores(q, index["embeddings"])
    return _topk(scores, index["docs"], k)


def retrieve_hybrid(query: str, index: dict | None = None, k: int | None = None) -> list[dict]:
    """Reciprocal rank fusion of dense + BM25."""
    index = index or build_index()
    k = k or config.RAG_TOP_K
    embedder = _embedder()
    q = embedder.encode([query])[0]
    dense = cosine_scores(q, index["embeddings"])
    sparse = bm25_scores(query, index["bm25"])

    # RRF
    n = len(index["docs"])
    rrf = np.zeros(n, dtype=np.float32)
    for rank, i in enumerate(np.argsort(-dense)):
        rrf[i] += 1.0 / (60 + rank + 1)
    for rank, i in enumerate(np.argsort(-sparse)):
        rrf[i] += 1.0 / (60 + rank + 1)
    return _topk(rrf, index["docs"], k)


def retrieve_filtered(
    query: str,
    *,
    asset_class: str | None = None,
    jurisdiction: str | None = None,
    track: str | None = None,
    index: dict | None = None,
    k: int | None = None,
) -> list[dict]:
    """Dense retrieve then keep chunks matching SDMX-like metadata filters."""
    index = index or build_index()
    k = k or config.RAG_TOP_K
    # Pull a wider pool then filter
    pool = retrieve_dense(query, index=index, k=max(k * 3, k))
    filtered = []
    for d in pool:
        if track and d.get("track") not in {track, "general"}:
            # allow cross-read of supervisory policy for risk questions
            if track == "risk" and d.get("track") == "supervisory":
                pass
            elif track == "treasury" and d.get("track") in {"risk", "supervisory"}:
                pass
            else:
                continue
        if asset_class and d.get("asset_classes"):
            if asset_class not in d["asset_classes"]:
                continue
        if jurisdiction and d.get("jurisdictions"):
            if jurisdiction not in d["jurisdictions"]:
                continue
        filtered.append(d)
    if len(filtered) < k:
        # backfill with unfiltered dense hits
        seen = {d["id"] for d in filtered}
        for d in pool:
            if d["id"] not in seen:
                filtered.append(d)
            if len(filtered) >= k:
                break
    return filtered[:k]


def retrieve_corrective(
    query: str,
    index: dict | None = None,
    k: int | None = None,
) -> list[dict]:
    """Retrieve → relevance check → re-query with missing keywords if weak."""
    index = index or build_index()
    k = k or config.RAG_TOP_K
    first = retrieve_hybrid(query, index=index, k=k)
    q_terms = set(query.lower().split())
    # crude coverage: fraction of query tokens appearing in top chunks
    joined = " ".join(d["text"].lower() for d in first)
    hit = sum(1 for t in q_terms if len(t) > 3 and t in joined)
    coverage = hit / max(sum(1 for t in q_terms if len(t) > 3), 1)
    if coverage >= 0.4:
        for d in first:
            d["corrective_pass"] = 1
            d["coverage"] = coverage
        return first

    # Expand query with typology keywords often missing from free-form questions
    expanded = query + " structuring sanctions layering liquidity buffer PSI anomaly"
    second = retrieve_hybrid(expanded, index=index, k=k)
    for d in second:
        d["corrective_pass"] = 2
        d["coverage"] = coverage
        d["expanded_query"] = expanded
    return second


def _build_graph(docs: list[dict]) -> dict[str, set[str]]:
    """Entity graph: topic/asset/jurisdiction → doc ids."""
    g: dict[str, set[str]] = {}
    for d in docs:
        nodes = (
            [f"track:{d.get('track')}"]
            + [f"topic:{t}" for t in d.get("topics") or []]
            + [f"asset:{a}" for a in d.get("asset_classes") or []]
            + [f"jur:{j}" for j in d.get("jurisdictions") or []]
        )
        for n in nodes:
            g.setdefault(n, set()).add(d["id"])
        # link doc node
        g.setdefault(f"doc:{d['id']}", set()).update(nodes)
    return g


def retrieve_graph(
    query: str,
    *,
    asset_class: str | None = None,
    jurisdiction: str | None = None,
    track: str | None = None,
    index: dict | None = None,
    k: int | None = None,
) -> list[dict]:
    """Seed graph nodes from filters + query tokens, collect neighbouring docs, re-rank dense."""
    index = index or build_index()
    k = k or config.RAG_TOP_K
    docs = index["docs"]
    by_id = {d["id"]: d for d in docs}
    graph = _build_graph(docs)

    seeds: list[str] = []
    if track:
        seeds.append(f"track:{track}")
    if asset_class:
        seeds.append(f"asset:{asset_class}")
    if jurisdiction:
        seeds.append(f"jur:{jurisdiction}")
    for tok in query.lower().replace("/", " ").split():
        if len(tok) > 3:
            seeds.append(f"topic:{tok}")

    candidate_ids: set[str] = set()
    for s in seeds:
        for doc_id in graph.get(s, set()):
            candidate_ids.add(doc_id)
        # one-hop via doc nodes
        for node in list(graph.get(s, set())):
            if node.startswith("doc:"):
                candidate_ids.add(node.split(":", 1)[1])

    if not candidate_ids:
        return retrieve_dense(query, index=index, k=k)

    embedder = _embedder()
    q = embedder.encode([query])[0]
    # score only candidates
    scores = np.full(len(docs), -1.0, dtype=np.float32)
    id_to_i = {d["id"]: i for i, d in enumerate(docs)}
    full = cosine_scores(q, index["embeddings"])
    for doc_id in candidate_ids:
        i = id_to_i.get(doc_id)
        if i is not None:
            scores[i] = full[i]
    hits = _topk(scores, docs, k)
    for h in hits:
        h["graph_seeds"] = seeds[:8]
    return hits


RETRIEVERS = {
    "dense": lambda q, **kw: retrieve_dense(q, **{k: v for k, v in kw.items() if k in {"index", "k"}}),
    "hybrid": lambda q, **kw: retrieve_hybrid(q, **{k: v for k, v in kw.items() if k in {"index", "k"}}),
    "filtered": retrieve_filtered,
    "corrective": lambda q, **kw: retrieve_corrective(q, **{k: v for k, v in kw.items() if k in {"index", "k"}}),
    "graph": retrieve_graph,
}


def retrieve(name: str, query: str, **kwargs) -> list[dict[str, Any]]:
    if name not in RETRIEVERS:
        raise KeyError(f"Unknown retriever: {name}")
    return RETRIEVERS[name](query, **kwargs)
