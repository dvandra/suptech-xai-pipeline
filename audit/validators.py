"""Pluggable validators for LLM XAI and RAG steps.

Register new validators via ``VALIDATORS`` for future pipelines without
changing the tracer or report writers.
"""
from __future__ import annotations

from typing import Any, Callable

from analytics.cot_steps import parse_steps, validate_steps
from audit.schema import ReasoningStep, ValidationCheck


def validate_llm_xai(record: dict[str, Any]) -> tuple[list[ReasoningStep], list[ValidationCheck]]:
    """Per-step CoT validation for Stage 4 explanations."""
    checks_raw = record.get("step_checks") or validate_steps(record)
    steps_map = record.get("steps") or parse_steps(record.get("explanation") or "")
    titles = {
        "STEP1": "Purpose vs asset class",
        "STEP2": "Amount plausibility",
        "STEP3": "Red-flag language",
        "STEP4": "Risk rating & action",
    }
    reasoning = [
        ReasoningStep(
            step_id=k,
            title=titles.get(k, k),
            detail=(steps_map.get(k) or "")[:500],
            evidence_refs=[record.get("id", "")] if record.get("id") else [],
        )
        for k in ("STEP1", "STEP2", "STEP3", "STEP4")
        if steps_map.get(k)
    ]
    mapping = [
        ("has_all_steps", "cot_all_steps_present", "All four CoT steps present"),
        ("step1_ok", "cot_step1_purpose_asset", "STEP1 covers purpose/asset"),
        ("step2_ok", "cot_step2_amount", "STEP2 covers amount/magnitude"),
        ("step3_ok", "cot_step3_red_flags", "STEP3 addresses red flags"),
        ("step4_ok", "cot_step4_rating_action", "STEP4 has rating + action"),
        ("all_steps_ok", "cot_all_steps_ok", "Full CoT contract satisfied"),
    ]
    validations = [
        ValidationCheck(
            check_id=cid,
            name=name,
            passed=bool(checks_raw.get(key)),
            severity="error",
            message="pass" if checks_raw.get(key) else "fail",
            meta={"rating": checks_raw.get("rating") or record.get("risk_rating")},
        )
        for key, cid, name in mapping
    ]
    # Rating parseability as explicit check
    rating = record.get("risk_rating") or checks_raw.get("rating")
    validations.append(
        ValidationCheck(
            check_id="cot_rating_parseable",
            name="Risk rating parseable (LOW/MEDIUM/HIGH)",
            passed=rating in {"LOW", "MEDIUM", "HIGH"},
            severity="error",
            message=str(rating or "UNRATED"),
        )
    )
    return reasoning, validations


def validate_rag_retrieve(row: dict[str, Any]) -> tuple[list[ReasoningStep], list[ValidationCheck]]:
    """Validate retrieval quality for one RAG case/retriever run."""
    retrieved = row.get("retrieved_ids") or []
    gold = row.get("gold_ids") or []
    scores = row.get("retrieved_scores") or []
    reasoning = [
        ReasoningStep(
            step_id="retrieve",
            title=f"Retriever={row.get('retriever')}",
            detail=f"top_k ids={retrieved}",
            evidence_refs=list(retrieved),
        )
    ]
    hit = any(g in retrieved for g in gold) if gold else bool(retrieved)
    validations = [
        ValidationCheck(
            check_id="rag_retrieve_nonempty",
            name="Retrieved at least one chunk",
            passed=len(retrieved) > 0,
            severity="error",
            message=f"n={len(retrieved)}",
        ),
        ValidationCheck(
            check_id="rag_retrieve_hit_at_k",
            name="Hit@k against gold chunk ids",
            passed=hit if gold else True,
            severity="error" if gold else "info",
            score=1.0 if hit else 0.0,
            message=f"retrieved={retrieved} gold={gold}",
            meta={"scores": scores[:5]},
        ),
    ]
    return reasoning, validations


def validate_rag_generate(row: dict[str, Any]) -> tuple[list[ReasoningStep], list[ValidationCheck]]:
    """Validate answer grounding / citations for one RAG generation."""
    answer = row.get("answer") or ""
    retrieved = row.get("retrieved_ids") or []
    must_terms = row.get("must_terms") or []
    cited = [rid for rid in retrieved if f"[{rid}]" in answer or rid in answer]
    term_hits = [t for t in must_terms if t.lower() in answer.lower()]
    reasoning = [
        ReasoningStep(
            step_id="generate",
            title=f"Model={row.get('model')} engine={row.get('engine')}",
            detail=answer[:600],
            evidence_refs=cited,
        )
    ]
    citation_rate = (len(cited) / len(retrieved)) if retrieved else 0.0
    term_cov = (len(term_hits) / len(must_terms)) if must_terms else 1.0
    validations = [
        ValidationCheck(
            check_id="rag_answer_nonempty",
            name="Answer text non-empty",
            passed=bool(answer.strip()),
            severity="error",
        ),
        ValidationCheck(
            check_id="rag_citation_present",
            name="At least one retrieved chunk cited",
            passed=len(cited) > 0 if retrieved else False,
            severity="error",
            score=round(citation_rate, 4),
            message=f"cited={cited}",
        ),
        ValidationCheck(
            check_id="rag_term_coverage",
            name="Required domain terms covered",
            passed=term_cov >= 0.5,
            severity="warn",
            score=round(term_cov, 4),
            message=f"hits={term_hits}",
        ),
        ValidationCheck(
            check_id="rag_faithfulness_proxy_gate",
            name="Faithfulness proxy >= 0.5",
            passed=float(row.get("faithfulness_proxy") or 0) >= 0.5,
            severity="error",
            score=row.get("faithfulness_proxy"),
        ),
    ]
    return reasoning, validations


def validate_detector_row(row: dict[str, Any]) -> tuple[list[ReasoningStep], list[ValidationCheck]]:
    """Lightweight audit for anomaly detector decisions (Stage 3)."""
    reasoning = [
        ReasoningStep(
            step_id="score",
            title="Anomaly score vs threshold decision",
            detail=(
                f"score={row.get('anomaly_score')} category={row.get('predicted_category')} "
                f"is_anomaly={row.get('is_anomaly')}"
            ),
            evidence_refs=[str(row.get("id", ""))],
        )
    ]
    validations = [
        ValidationCheck(
            check_id="detector_score_present",
            name="Anomaly score present",
            passed=row.get("anomaly_score") is not None,
            severity="error",
        ),
        ValidationCheck(
            check_id="detector_category_present",
            name="Predicted category present",
            passed=bool(row.get("predicted_category")),
            severity="warn",
        ),
    ]
    return reasoning, validations


ValidatorFn = Callable[
    [dict[str, Any]], tuple[list[ReasoningStep], list[ValidationCheck]]
]

# Registry — extend for future use cases without changing callers.
VALIDATORS: dict[str, ValidatorFn] = {
    "llm_xai": validate_llm_xai,
    "rag_retrieve": validate_rag_retrieve,
    "rag_generate": validate_rag_generate,
    "detector": validate_detector_row,
}


def run_validator(
    name: str, payload: dict[str, Any]
) -> tuple[list[ReasoningStep], list[ValidationCheck]]:
    if name not in VALIDATORS:
        raise KeyError(f"Unknown validator: {name}. Known: {sorted(VALIDATORS)}")
    return VALIDATORS[name](payload)
