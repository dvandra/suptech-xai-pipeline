"""Stage 4 - Explainable AI (XAI) for flagged anomalies.

For each record flagged by stage 3, a local LLM is prompted with a strict
Chain-of-Thought (CoT) template to produce a transparent, auditable
justification for why the transaction is anomalous - so supervisors get a
human-readable rationale rather than an opaque score.

  * Primary: LangChain + a local Ollama model (fully on-prem, no data egress).
  * Fallback: a deterministic, rule-based CoT explainer so the report is still
    generated when no LLM runtime is present.

Output is a Markdown compliance report at ``data/reports/anomaly_report.md``.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

_RATING_RE = re.compile(r"\b(LOW|MEDIUM|HIGH)\b")


def _parse_rating(text: str) -> str:
    """Extract the risk rating from an explanation (last mention wins)."""
    matches = _RATING_RE.findall(text.upper())
    return matches[-1] if matches else "UNRATED"

COT_PROMPT = """You are a financial supervision assistant for a central bank.
Analyse the following transaction submission and explain, step by step, whether
it is anomalous and why. Be precise and auditable.

Transaction:
- ID: {id}
- Reporting area: {ref_area}
- Institution: {institution_id}
- Asset class: {asset_class}
- Period: {time_period}
- Amount: {obs_value} {currency}
- Stated purpose: "{txn_purpose}"
- Model-assigned category: {predicted_category}
- Anomaly score (distance to nearest category centroid): {anomaly_score}

Reason step by step:
1. Assess whether the stated purpose is consistent with the asset class.
2. Assess whether the amount is plausible for this kind of activity.
3. Note any red-flag language (e.g. sanctions evasion, structuring, layering).
4. Conclude with a clear risk rating (LOW / MEDIUM / HIGH) and recommended action.
"""


def _ollama_explain(rec: dict) -> str | None:
    try:
        from langchain_ollama import OllamaLLM
    except Exception:
        try:
            from langchain_community.llms import Ollama as OllamaLLM  # type: ignore
        except Exception:
            return None
    try:
        llm = OllamaLLM(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
        return llm.invoke(COT_PROMPT.format(**rec)).strip()
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
    purpose = str(rec["txn_purpose"]).lower()
    hits = [msg for kw, msg in _RED_FLAGS if kw in purpose]
    large = rec["obs_value"] >= 50_000_000

    steps = [
        f"1. The stated purpose is categorised as `{rec['predicted_category']}`; "
        f"its wording sits far from typical {rec['asset_class']} activity "
        f"(anomaly score {rec['anomaly_score']}, above the alert threshold).",
        f"2. The amount is {rec['obs_value']:,.0f} {rec['currency']}, which is "
        + ("unusually large for this activity type." if large else "within a plausible range, so magnitude alone is not decisive."),
    ]
    if hits:
        steps.append("3. Red-flag language detected: " + "; ".join(hits) + ".")
        rating, action = "HIGH", "Escalate to the AML/financial-crime unit and file for review."
    elif large:
        steps.append("3. No explicit red-flag language, but the size warrants scrutiny.")
        rating, action = "MEDIUM", "Request supporting documentation from the institution."
    else:
        steps.append("3. No explicit red-flag language identified.")
        rating, action = "MEDIUM", "Queue for analyst confirmation of the semantic outlier."
    steps.append(f"4. Risk rating: **{rating}**. Recommended action: {action}")
    return "\n".join(steps)


def run() -> dict:
    config.ensure_dirs()
    if not config.CLASSIFIED_JSONL.exists():
        sys.exit(f"{config.CLASSIFIED_JSONL} not found. Run stage 3 first.")

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
        f"Flagged observations: **{len(anomalies)}**",
        "",
        "Each explanation is produced by Chain-of-Thought reasoning over a "
        "local model, keeping supervisory data on-premises.",
        "",
    ]

    used_llm = False
    structured = []
    for rec in anomalies:
        explanation = _ollama_explain(rec)
        if explanation is None:
            explanation = _rule_based_explain(rec)
            engine = "rule-based"
        else:
            used_llm = True
            engine = "ollama"
        rating = _parse_rating(explanation)
        lines += [
            f"## {rec['id']} - {rec['ref_area']} / {rec['asset_class']}",
            f"**Amount:** {rec['obs_value']:,.2f} {rec['currency']}  ",
            f"**Stated purpose:** {rec['txn_purpose']}  ",
            f"**Anomaly score:** {rec['anomaly_score']} | **Risk rating:** {rating}",
            "",
            explanation,
            "",
            "---",
            "",
        ]
        structured.append(
            {
                "id": rec["id"],
                "ref_area": rec["ref_area"],
                "asset_class": rec["asset_class"],
                "obs_value": rec["obs_value"],
                "currency": rec["currency"],
                "txn_purpose": rec["txn_purpose"],
                "predicted_category": rec["predicted_category"],
                "anomaly_score": rec["anomaly_score"],
                "risk_rating": rating,
                "explanation": explanation,
                "engine": engine,
            }
        )

    config.ANOMALY_REPORT.write_text("\n".join(lines))
    with config.EXPLANATIONS_JSONL.open("w") as fh:
        for row in structured:
            fh.write(json.dumps(row) + "\n")

    engine = "Ollama LLM" if used_llm else "rule-based fallback"
    print(
        f"[explain] wrote {len(anomalies)} explanations ({engine}) "
        f"-> {config.ANOMALY_REPORT}, {config.EXPLANATIONS_JSONL}"
    )
    return {"anomalies": len(anomalies), "engine": engine}


if __name__ == "__main__":
    run()
