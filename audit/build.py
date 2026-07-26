"""Build audit trails from existing pipeline artefacts (and live runs)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config
from audit.tracer import AuditTracer
from audit.validators import run_validator


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open() as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def audit_explanations(
    tracer: AuditTracer,
    explanations: list[dict[str, Any]] | None = None,
) -> int:
    """Emit one audit event per Stage-4 XAI explanation."""
    exps = explanations if explanations is not None else _load_jsonl(config.EXPLANATIONS_JSONL)
    for exp in exps:
        reasoning, validations = run_validator("llm_xai", exp)
        tracer.step(
            pipeline="llm_xai",
            stage="stage4_explain",
            step_name="cot_explain",
            subject_id=str(exp.get("id", "")),
            model=exp.get("model"),
            prompt_version=exp.get("prompt_version"),
            engine=exp.get("engine"),
            inputs={
                "txn_purpose": exp.get("txn_purpose"),
                "asset_class": exp.get("asset_class"),
                "obs_value": exp.get("obs_value"),
                "anomaly_score": exp.get("anomaly_score"),
            },
            outputs={
                "risk_rating": exp.get("risk_rating"),
                "explanation": (exp.get("explanation") or "")[:800],
            },
            reasoning_steps=reasoning,
            validations=validations,
            meta={"step_checks": exp.get("step_checks")},
        )
    return len(exps)


def audit_detector(
    tracer: AuditTracer,
    classified: list[dict[str, Any]] | None = None,
    anomalies_only: bool = True,
) -> int:
    """Emit audit events for detector decisions (flagged rows by default)."""
    rows = classified if classified is not None else _load_jsonl(config.CLASSIFIED_JSONL)
    n = 0
    for row in rows:
        if anomalies_only and not row.get("is_anomaly"):
            continue
        reasoning, validations = run_validator("detector", row)
        tracer.step(
            pipeline="detector",
            stage="stage3_classify",
            step_name="anomaly_decision",
            subject_id=str(row.get("id", "")),
            engine="embeddings",
            inputs={
                "txn_purpose": row.get("txn_purpose"),
                "asset_class": row.get("asset_class"),
            },
            outputs={
                "anomaly_score": row.get("anomaly_score"),
                "is_anomaly": row.get("is_anomaly"),
                "predicted_category": row.get("predicted_category"),
            },
            reasoning_steps=reasoning,
            validations=validations,
        )
        n += 1
    return n


def audit_rag_results(
    tracer: AuditTracer,
    results: list[dict[str, Any]] | None = None,
) -> int:
    """Emit retrieve + generate audit events for each RAG scored row."""
    if results is None:
        if not config.RAG_RESULTS_JSON.exists():
            return 0
        payload = json.loads(config.RAG_RESULTS_JSON.read_text())
        results = payload.get("results") or []

    for row in results:
        subject = (
            f"{row.get('case_id')}:{row.get('retriever')}:{row.get('model')}"
        )
        # Retrieve step
        r_reason, r_vals = run_validator("rag_retrieve", row)
        tracer.step(
            pipeline="rag",
            stage="stage6_rag_retrieve",
            step_name="retrieve",
            subject_id=subject,
            model=row.get("model"),
            engine=row.get("retriever"),
            inputs={
                "question": row.get("question"),
                "track": row.get("track"),
                "gold_ids": row.get("gold_ids"),
            },
            outputs={"retrieved_ids": row.get("retrieved_ids")},
            reasoning_steps=r_reason,
            validations=r_vals,
            meta={"retriever": row.get("retriever")},
        )
        # Generate step
        g_reason, g_vals = run_validator("rag_generate", row)
        tracer.step(
            pipeline="rag",
            stage="stage6_rag_generate",
            step_name="generate",
            subject_id=subject,
            model=row.get("model"),
            engine=row.get("engine"),
            inputs={
                "question": row.get("question"),
                "retrieved_ids": row.get("retrieved_ids"),
            },
            outputs={
                "answer": (row.get("answer") or "")[:800],
                "faithfulness_proxy": row.get("faithfulness_proxy"),
                "citation_rate": row.get("citation_rate"),
            },
            reasoning_steps=g_reason,
            validations=g_vals,
            meta={"track": row.get("track"), "retriever": row.get("retriever")},
        )
    return len(results)


def build_full_audit(run_id: str | None = None) -> tuple[AuditTracer, dict[str, Any]]:
    """Build a complete audit trail from current data/ artefacts."""
    tracer = AuditTracer(run_id=run_id, pipeline="suptech-xai")
    counts = {
        "detector": audit_detector(tracer),
        "llm_xai": audit_explanations(tracer),
        "rag_cases": audit_rag_results(tracer),
    }
    summary = tracer.flush()
    summary["source_counts"] = counts
    config.AUDIT_SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str))
    return tracer, summary
