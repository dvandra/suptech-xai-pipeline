"""Evaluate RAG retrieval + answer quality across retrievers and models."""
from __future__ import annotations

from typing import Any


def _hit_at_k(retrieved: list[str], gold: list[str]) -> float:
    return 1.0 if any(g in retrieved for g in gold) else 0.0


def _recall_at_k(retrieved: list[str], gold: list[str]) -> float:
    if not gold:
        return 0.0
    return sum(1 for g in gold if g in retrieved) / len(gold)


def _citation_rate(answer: str, retrieved: list[str]) -> float:
    if not retrieved:
        return 0.0
    hits = sum(1 for rid in retrieved if f"[{rid}]" in answer or rid in answer)
    return hits / len(retrieved)


def _term_coverage(answer: str, must_terms: list[str]) -> float:
    if not must_terms:
        return 1.0
    a = answer.lower()
    return sum(1 for t in must_terms if t.lower() in a) / len(must_terms)


def score_result(row: dict[str, Any]) -> dict[str, Any]:
    retrieved = row.get("retrieved_ids") or []
    gold = row.get("gold_ids") or []
    answer = row.get("answer") or ""
    return {
        **row,
        "hit_at_k": _hit_at_k(retrieved, gold),
        "recall_at_k": round(_recall_at_k(retrieved, gold), 4),
        "citation_rate": round(_citation_rate(answer, retrieved), 4),
        "term_coverage": round(_term_coverage(answer, row.get("must_terms") or []), 4),
        "faithfulness_proxy": round(
            0.5 * _hit_at_k(retrieved, gold)
            + 0.3 * _citation_rate(answer, retrieved)
            + 0.2 * _term_coverage(answer, row.get("must_terms") or []),
            4,
        ),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    keys = ["hit_at_k", "recall_at_k", "citation_rate", "term_coverage", "faithfulness_proxy"]
    summary = {k: round(sum(r[k] for r in rows) / len(rows), 4) for k in keys}
    summary["n"] = len(rows)

    by_retriever: dict[str, list] = {}
    by_model: dict[str, list] = {}
    by_track: dict[str, list] = {}
    for r in rows:
        by_retriever.setdefault(r["retriever"], []).append(r)
        by_model.setdefault(r["model"], []).append(r)
        by_track.setdefault(r["track"], []).append(r)

    def _avg(group: list[dict]) -> dict:
        return {k: round(sum(x[k] for x in group) / len(group), 4) for k in keys} | {
            "n": len(group)
        }

    return {
        "overall": summary,
        "by_retriever": {k: _avg(v) for k, v in by_retriever.items()},
        "by_model": {k: _avg(v) for k, v in by_model.items()},
        "by_track": {k: _avg(v) for k, v in by_track.items()},
    }
