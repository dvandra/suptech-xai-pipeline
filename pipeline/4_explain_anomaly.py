"""Stage 4 - Explainable AI (XAI) for flagged anomalies.

For each record flagged by stage 3, a local LLM is prompted with a strict
Chain-of-Thought (CoT) template to produce a transparent, auditable
justification for why the transaction is anomalous - so supervisors get a
human-readable rationale rather than an opaque score.

  * Primary: LangChain + a local Ollama model (fully on-prem, no data egress).
  * Fallback: a deterministic, rule-based CoT explainer so the report is still
    generated when no LLM runtime is present.

Prompt versions (``config.PROMPT_VERSION``):
  * v1 - free-form numbered steps
  * v2 - labelled STEP1..STEP4 contract (default; easier to validate)

Output:
  * ``data/reports/anomaly_report.md``
  * ``data/explanations.jsonl`` (includes parsed steps + prompt_version)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from analytics.cot_steps import (  # noqa: E402
    parse_rating,
    parse_steps,
    prompt_for_version,
    validate_steps,
)


def _ollama_explain(rec: dict, prompt_version: str) -> str | None:
    try:
        from langchain_ollama import OllamaLLM
    except Exception:
        try:
            from langchain_community.llms import Ollama as OllamaLLM  # type: ignore
        except Exception:
            return None
    try:
        llm = OllamaLLM(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
        template = prompt_for_version(prompt_version)
        return llm.invoke(template.format(**rec)).strip()
    except Exception as exc:
        print(f"[explain] Ollama unavailable ({exc}); using rule-based fallback")
        return None


# Vocabulary that signals elevated financial-crime risk.
_RED_FLAGS = [
    ("sanction", "counterparty linked to sanctions"),
    ("shell", "transfer to an opaque shell entity"),
    ("structuring", "structuring to evade reporting thresholds"),
    ("threshold", "activity engineered around reporting thresholds"),
    ("layering", "layering consistent with money-laundering typologies"),
    ("round-trip", "round-tripping of funds across jurisdictions"),
    ("mis-invoic", "trade mis-invoicing to move value"),
    ("unregistered", "dealing with an unregistered entity"),
    ("offshore", "unexplained offshore routing"),
]


def _rule_based_explain(rec: dict) -> str:
    """Deterministic CoT that already obeys the v2 STEP labels."""
    purpose = str(rec["txn_purpose"]).lower()
    hits = [msg for kw, msg in _RED_FLAGS if kw in purpose]
    cited = [kw for kw, _ in _RED_FLAGS if kw in purpose]
    large = rec["obs_value"] >= 50_000_000

    step1 = (
        f"The stated purpose is categorised as `{rec['predicted_category']}`; "
        f"its wording sits far from typical {rec['asset_class']} activity "
        f"(anomaly score {rec['anomaly_score']}, above the alert threshold)."
    )
    step2 = (
        f"The amount is {rec['obs_value']:,.0f} {rec['currency']}, which is "
        + (
            "unusually large for this activity type."
            if large
            else "within a plausible range, so magnitude alone is not decisive."
        )
    )
    if hits:
        step3 = "Red-flag language detected (" + ", ".join(cited) + "): " + "; ".join(hits) + "."
        rating, action = (
            "HIGH",
            "Escalate to the AML/financial-crime unit and file for review.",
        )
    elif large:
        step3 = "No explicit red-flag language, but the size warrants scrutiny."
        rating, action = (
            "MEDIUM",
            "Request supporting documentation from the institution.",
        )
    else:
        step3 = "No explicit red-flag language identified."
        rating, action = (
            "MEDIUM",
            "Queue for analyst confirmation of the semantic outlier.",
        )
    step4 = f"Risk rating: {rating}. Recommended action: {action}"
    return (
        f"STEP1: {step1}\n"
        f"STEP2: {step2}\n"
        f"STEP3: {step3}\n"
        f"STEP4: {step4}"
    )


def run() -> dict:
    config.ensure_dirs()
    if not config.CLASSIFIED_JSONL.exists():
        sys.exit(f"{config.CLASSIFIED_JSONL} not found. Run stage 3 first.")

    prompt_version = config.PROMPT_VERSION
    anomalies = []
    with config.CLASSIFIED_JSONL.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("is_anomaly"):
                anomalies.append(rec)

    lines = [
        "# SupTech-XAI Anomaly Report",
        "",
        f"Dataflow: `{config.DATAFLOW_REF}`  ",
        f"Prompt version: `{prompt_version}`  ",
        f"Explain model: `{config.OLLAMA_MODEL}` (fallback: rule-based)  ",
        f"Flagged observations: **{len(anomalies)}**",
        "",
        "Each explanation uses a four-step Chain-of-Thought contract "
        "(purpose vs asset class → amount → red flags → rating/action).",
        "",
    ]

    used_llm = False
    structured = []
    step_pass = 0
    for rec in anomalies:
        explanation = _ollama_explain(rec, prompt_version)
        if explanation is None:
            explanation = _rule_based_explain(rec)
            engine = "rule-based"
        else:
            used_llm = True
            engine = "ollama"
        rating = parse_rating(explanation)
        steps = parse_steps(explanation)
        row = {
            "id": rec["id"],
            "ref_area": rec["ref_area"],
            "institution_id": rec.get("institution_id"),
            "asset_class": rec["asset_class"],
            "time_period": rec.get("time_period"),
            "obs_value": rec["obs_value"],
            "currency": rec["currency"],
            "txn_purpose": rec["txn_purpose"],
            "predicted_category": rec["predicted_category"],
            "anomaly_score": rec["anomaly_score"],
            "risk_rating": rating,
            "explanation": explanation,
            "steps": steps,
            "engine": engine,
            "prompt_version": prompt_version,
            "model": config.OLLAMA_MODEL if engine == "ollama" else "rule-based",
        }
        checks = validate_steps(row)
        row["step_checks"] = {
            k: checks[k]
            for k in (
                "has_all_steps",
                "step1_ok",
                "step2_ok",
                "step3_ok",
                "step4_ok",
                "all_steps_ok",
            )
        }
        if checks["all_steps_ok"]:
            step_pass += 1

        lines += [
            f"## {rec['id']} - {rec['ref_area']} / {rec['asset_class']}",
            f"**Amount:** {rec['obs_value']:,.2f} {rec['currency']}  ",
            f"**Stated purpose:** {rec['txn_purpose']}  ",
            f"**Anomaly score:** {rec['anomaly_score']} | **Risk rating:** {rating}  ",
            f"**Step validation:** "
            f"{'PASS' if checks['all_steps_ok'] else 'FAIL'}",
            "",
            explanation,
            "",
            "---",
            "",
        ]
        structured.append(row)

    config.ANOMALY_REPORT.write_text("\n".join(lines))
    with config.EXPLANATIONS_JSONL.open("w") as fh:
        for row in structured:
            fh.write(json.dumps(row) + "\n")

    engine = "Ollama LLM" if used_llm else "rule-based fallback"
    print(
        f"[explain] wrote {len(anomalies)} explanations ({engine}, prompt={prompt_version}) "
        f"step-pass={step_pass}/{len(anomalies)} "
        f"-> {config.ANOMALY_REPORT}, {config.EXPLANATIONS_JSONL}"
    )
    return {
        "anomalies": len(anomalies),
        "engine": engine,
        "prompt_version": prompt_version,
        "step_pass": step_pass,
    }


if __name__ == "__main__":
    run()
