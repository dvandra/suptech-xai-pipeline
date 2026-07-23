"""Shared helpers for structured Chain-of-Thought step parsing & checks.

Used by Stage 4 (explain) and Stage 5 (evaluation) so the prompt contract and
the validators stay in sync.
"""
from __future__ import annotations

import re
from typing import Any

import config

# Prompt contract versions. v2 requires labelled STEP1..STEP4 blocks.
PROMPT_VERSION_V1 = "v1"
PROMPT_VERSION_V2 = "v2"

STEP_KEYS = ("STEP1", "STEP2", "STEP3", "STEP4")

_STEP_SPLIT_RE = re.compile(
    r"(?:^|\n)\s*(?:STEP\s*([1-4])\s*[:.\-–—]|\b([1-4])\s*[.)])\s*",
    re.IGNORECASE,
)
_RATING_RE = re.compile(r"\b(LOW|MEDIUM|HIGH)\b")


def parse_rating(text: str) -> str:
    matches = _RATING_RE.findall(text.upper())
    return matches[-1] if matches else "UNRATED"


def parse_steps(text: str) -> dict[str, str]:
    """Split an explanation into STEP1..STEP4 bodies (best-effort)."""
    text = (text or "").strip()
    if not text:
        return {}

    parts = _STEP_SPLIT_RE.split(text)
    # parts: [preamble, n_or_None, n_or_None, body, n, n, body, ...]
    steps: dict[str, str] = {}
    i = 1
    while i + 1 < len(parts):
        n = parts[i] or parts[i + 1]
        body = parts[i + 2].strip() if i + 2 < len(parts) else ""
        if n in "1234":
            steps[f"STEP{n}"] = body
        i += 3
    return steps


def validate_steps(exp: dict[str, Any]) -> dict[str, Any]:
    """Per-step pass/fail checks for one explanation record."""
    explanation = exp.get("explanation") or ""
    steps = exp.get("steps") or parse_steps(explanation)
    purpose = str(exp.get("txn_purpose", ""))
    purpose_l = purpose.lower()
    present_flags = [t for t in config.RED_FLAG_TERMS if t in purpose_l]
    rating = exp.get("risk_rating") or parse_rating(explanation)

    results: dict[str, Any] = {
        "has_all_steps": all(k in steps and steps[k].strip() for k in STEP_KEYS),
        "step_count": sum(1 for k in STEP_KEYS if steps.get(k, "").strip()),
        "rating_ok": rating in {"LOW", "MEDIUM", "HIGH"},
        "rating": rating,
        "present_red_flags": present_flags,
    }

    s1 = steps.get("STEP1", "").lower()
    s2 = steps.get("STEP2", "").lower()
    s3 = steps.get("STEP3", "").lower()
    s4 = steps.get("STEP4", "").lower()

    asset = str(exp.get("asset_class", "")).lower()
    results["step1_ok"] = bool(s1) and (
        asset in s1
        or "purpose" in s1
        or "asset" in s1
        or "categor" in s1
        or "consistent" in s1
        or "inconsistent" in s1
    )

    amount_hint = str(int(float(exp.get("obs_value", 0) or 0)))[:3]
    currency = str(exp.get("currency", "")).lower()
    results["step2_ok"] = bool(s2) and (
        "amount" in s2
        or "plausible" in s2
        or "large" in s2
        or "magnitude" in s2
        or currency in s2
        or (amount_hint and amount_hint in s2.replace(",", ""))
    )

    if present_flags:
        results["step3_ok"] = bool(s3) and any(t in s3 for t in present_flags)
    else:
        results["step3_ok"] = bool(s3)

    results["step4_ok"] = bool(s4) and (
        results["rating_ok"]
        and (
            "action" in s4
            or "escalat" in s4
            or "request" in s4
            or "review" in s4
            or "queue" in s4
            or "rating" in s4
        )
    )

    results["all_steps_ok"] = all(
        results[k]
        for k in ("step1_ok", "step2_ok", "step3_ok", "step4_ok", "has_all_steps")
    )
    return results


COT_PROMPT_V1 = """You are a financial supervision assistant for a central bank.
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


COT_PROMPT_V2 = """You are a financial supervision assistant for a central bank.
Analyse the following transaction submission. Be precise and auditable.

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

You MUST respond using exactly these four labelled blocks (no other preamble):
STEP1: Assess whether the stated purpose is consistent with the asset class.
STEP2: Assess whether the amount is plausible for this kind of activity.
STEP3: Note any red-flag language present in the purpose (quote the terms you rely on).
STEP4: Conclude with a clear risk rating (LOW / MEDIUM / HIGH) and a recommended action.
"""


def prompt_for_version(version: str) -> str:
    return COT_PROMPT_V2 if version == PROMPT_VERSION_V2 else COT_PROMPT_V1
