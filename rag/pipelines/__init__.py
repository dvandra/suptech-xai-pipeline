"""Stage 6 question banks + pipeline runners for three finance tracks."""
from __future__ import annotations

from typing import Any

import config
from rag.index import build_index
from rag.llm import answer_with_context
from rag.retrievers import retrieve

# Gold chunk IDs used for retrieval evaluation (synthetic, known a priori).
CASES: list[dict[str, Any]] = [
    {
        "id": "SUP-1",
        "track": "supervisory",
        "question": (
            "A submission purpose mentions structuring cash below reporting "
            "thresholds. Which typology applies and what action is recommended?"
        ),
        "gold_ids": ["POL-AML-001"],
        "asset_class": "DEPOSIT",
        "jurisdiction": "US",
        "must_terms": ["structuring", "threshold"],
    },
    {
        "id": "SUP-2",
        "track": "supervisory",
        "question": (
            "Purpose text cites a sanctioned counterparty via an intermediary. "
            "How should supervisors rate and escalate this?"
        ),
        "gold_ids": ["POL-SAN-002"],
        "asset_class": "FX",
        "jurisdiction": "GB",
        "must_terms": ["sanction", "HIGH"],
    },
    {
        "id": "SUP-3",
        "track": "supervisory",
        "question": (
            "Why must SDMX structural validation succeed before semantic AI "
            "anomaly detection runs?"
        ),
        "gold_ids": ["POL-SDMX-003"],
        "asset_class": "LOAN",
        "jurisdiction": "DE",
        "must_terms": ["structural", "validation"],
    },
    {
        "id": "RISK-1",
        "track": "risk",
        "question": (
            "Anomaly scores cluster in a few institutions and PSI on categories "
            "is above 0.2. What risk narrative should analysts write?"
        ),
        "gold_ids": ["RISK-CONC-010"],
        "asset_class": "LOAN",
        "jurisdiction": "FR",
        "must_terms": ["PSI", "concentration"],
    },
    {
        "id": "RISK-2",
        "track": "risk",
        "question": (
            "Explain the drivers of an elevated embedding-based risk score when "
            "purpose language includes layering and extreme amounts."
        ),
        "gold_ids": ["RISK-PRED-011", "POL-AML-001"],
        "asset_class": "FX",
        "jurisdiction": "SG",
        "must_terms": ["driver", "embedding"],
    },
    {
        "id": "RISK-3",
        "track": "risk",
        "question": (
            "How does trade mis-invoicing appear in cross-border purpose text "
            "and which asset classes are commonly affected?"
        ),
        "gold_ids": ["RISK-TRADE-012"],
        "asset_class": "FX",
        "jurisdiction": "CH",
        "must_terms": ["mis-invoic", "cross-border"],
    },
    {
        "id": "TRY-1",
        "track": "treasury",
        "question": (
            "Large short-dated deposits mature in the same period. Explain roll "
            "risk and what a liquidity-buffer narrative should cite."
        ),
        "gold_ids": ["TRY-LIQ-020"],
        "asset_class": "DEPOSIT",
        "jurisdiction": "US",
        "must_terms": ["liquidity", "roll"],
    },
    {
        "id": "TRY-2",
        "track": "treasury",
        "question": (
            "When is an FX remittance or swap-line drawdown routine versus a "
            "currency-mismatch exception needing review?"
        ),
        "gold_ids": ["TRY-FX-021"],
        "asset_class": "FX",
        "jurisdiction": "JP",
        "must_terms": ["FX", "swap"],
    },
    {
        "id": "TRY-3",
        "track": "treasury",
        "question": (
            "How should treasury commentary separate normal IRS/bond rate "
            "activity from financial-crime typology language?"
        ),
        "gold_ids": ["TRY-RATE-022"],
        "asset_class": "DERIVATIVE",
        "jurisdiction": "GB",
        "must_terms": ["rate", "HIGH"],
    },
]


def run_case(
    case: dict[str, Any],
    *,
    retriever: str,
    model: str,
    index: dict | None = None,
) -> dict[str, Any]:
    index = index or build_index()
    kwargs: dict[str, Any] = {
        "index": index,
        "k": config.RAG_TOP_K,
    }
    if retriever in {"filtered", "graph"}:
        kwargs.update(
            {
                "asset_class": case.get("asset_class"),
                "jurisdiction": case.get("jurisdiction"),
                "track": case.get("track"),
            }
        )
    chunks = retrieve(retriever, case["question"], **kwargs)
    gen = answer_with_context(
        case["question"],
        chunks,
        track=case["track"],
        model=model,
        base_url=config.OLLAMA_BASE_URL,
    )
    return {
        "case_id": case["id"],
        "track": case["track"],
        "question": case["question"],
        "retriever": retriever,
        "model": model,
        "gold_ids": case["gold_ids"],
        "must_terms": case.get("must_terms") or [],
        "retrieved_ids": [c["id"] for c in chunks],
        "retrieved_scores": [round(c.get("score", 0.0), 4) for c in chunks],
        "answer": gen["answer"],
        "engine": gen["engine"],
    }
