"""Markdown comparison report for Stage 6 RAG exploration."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import config


def render(payload: dict) -> str:
    cfg = payload.get("config", {})
    summary = payload.get("summary", {})
    overall = summary.get("overall", {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# SupTech-XAI — RAG & LLM Comparison Report",
        "",
        f"_Generated {now}_",
        "",
        "Compares **dense**, **hybrid**, **metadata-filtered**, **corrective**, "
        "and **graph** retrievers across **supervisory analysis**, **risk "
        "narrative**, and **treasury / liquidity** question tracks. Synthetic "
        "corpus only.",
        "",
        "See [`docs/RAG_AND_MODELS.md`](../../docs/RAG_AND_MODELS.md).",
        "",
        "## Run config",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Retrievers | {', '.join(cfg.get('retrievers') or [])} |",
        f"| Models | {', '.join(cfg.get('models') or [])} |",
        f"| Top-k | {cfg.get('top_k')} |",
        f"| Embedder | `{cfg.get('embedder')}` |",
        f"| Corpus docs | {cfg.get('corpus_docs')} |",
        "",
        "## Overall metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| n (case × retriever × model) | {overall.get('n', 0)} |",
        f"| Hit@k | {overall.get('hit_at_k')} |",
        f"| Recall@k | {overall.get('recall_at_k')} |",
        f"| Citation rate | {overall.get('citation_rate')} |",
        f"| Term coverage | {overall.get('term_coverage')} |",
        f"| Faithfulness proxy | {overall.get('faithfulness_proxy')} |",
        "",
        "## By retriever",
        "",
        "| Retriever | Hit@k | Recall@k | Citation | Faithfulness | n |",
        "|---|---|---|---|---|---|",
    ]
    for name, m in (summary.get("by_retriever") or {}).items():
        lines.append(
            f"| {name} | {m.get('hit_at_k')} | {m.get('recall_at_k')} | "
            f"{m.get('citation_rate')} | {m.get('faithfulness_proxy')} | {m.get('n')} |"
        )

    lines += [
        "",
        "## By model",
        "",
        "| Model | Hit@k | Recall@k | Citation | Faithfulness | n |",
        "|---|---|---|---|---|---|",
    ]
    for name, m in (summary.get("by_model") or {}).items():
        lines.append(
            f"| {name} | {m.get('hit_at_k')} | {m.get('recall_at_k')} | "
            f"{m.get('citation_rate')} | {m.get('faithfulness_proxy')} | {m.get('n')} |"
        )

    lines += [
        "",
        "## By track",
        "",
        "| Track | Hit@k | Recall@k | Citation | Faithfulness | n |",
        "|---|---|---|---|---|---|",
    ]
    for name, m in (summary.get("by_track") or {}).items():
        lines.append(
            f"| {name} | {m.get('hit_at_k')} | {m.get('recall_at_k')} | "
            f"{m.get('citation_rate')} | {m.get('faithfulness_proxy')} | {m.get('n')} |"
        )

    # Sample failures / wins
    results = payload.get("results") or []
    weak = sorted(results, key=lambda r: r.get("faithfulness_proxy", 0))[:5]
    strong = sorted(results, key=lambda r: -r.get("faithfulness_proxy", 0))[:5]

    lines += ["", "## Strongest runs (sample)", ""]
    for r in strong:
        lines.append(
            f"- `{r['case_id']}` / {r['retriever']} / {r['model']} "
            f"faithfulness={r.get('faithfulness_proxy')} "
            f"retrieved={r.get('retrieved_ids')}"
        )
    lines += ["", "## Weakest runs (sample)", ""]
    for r in weak:
        lines.append(
            f"- `{r['case_id']}` / {r['retriever']} / {r['model']} "
            f"faithfulness={r.get('faithfulness_proxy')} "
            f"retrieved={r.get('retrieved_ids')} gold={r.get('gold_ids')}"
        )

    lines += [
        "",
        "## Artefacts",
        "",
        f"- Results JSON: `{config.RAG_RESULTS_JSON.relative_to(config.ROOT)}`",
        f"- This report: `{config.RAG_COMPARISON_MD.relative_to(config.ROOT)}`",
        "",
        "---",
        "",
        "_Synthetic data only · educational simulation._",
        "",
    ]
    return "\n".join(lines)


def write_comparison_report(payload: dict) -> Path:
    config.ensure_dirs()
    text = render(payload)
    config.RAG_COMPARISON_MD.write_text(text)
    return config.RAG_COMPARISON_MD
