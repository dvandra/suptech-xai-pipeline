"""Stage 6 orchestrator — multi-retriever × multi-model RAG comparison.

    python -m rag.run_rag
    make rag
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from analytics.charts import write_charts  # noqa: E402
from rag.evaluate_rag import aggregate, score_result  # noqa: E402
from rag.index import build_index  # noqa: E402
from rag.pipelines import CASES, run_case  # noqa: E402
from rag.report import write_comparison_report  # noqa: E402


def run(
    retrievers: list[str] | None = None,
    models: list[str] | None = None,
) -> dict:
    config.ensure_dirs()
    retrievers = retrievers or list(config.RAG_RETRIEVERS)
    models = models or list(config.RAG_MODELS)

    print("[rag] building corpus index...")
    index = build_index(force=True)
    print(
        f"[rag] docs={len(index['docs'])} embedder={index['embedder_name']} "
        f"retrievers={retrievers} models={models}"
    )

    rows = []
    total = len(CASES) * len(retrievers) * len(models)
    done = 0
    for case in CASES:
        for retriever in retrievers:
            for model in models:
                row = run_case(case, retriever=retriever, model=model, index=index)
                rows.append(score_result(row))
                done += 1
                if done % 9 == 0 or done == total:
                    print(f"[rag] progress {done}/{total}")

    summary = aggregate(rows)
    payload = {
        "config": {
            "retrievers": retrievers,
            "models": models,
            "top_k": config.RAG_TOP_K,
            "embedder": index["embedder_name"],
            "corpus_docs": len(index["docs"]),
        },
        "summary": summary,
        "results": rows,
    }
    config.RAG_RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str))
    write_comparison_report(payload)
    # Refresh chart gallery with latest RAG (+ existing metrics/audit if present)
    write_charts(rag=payload)
    overall = summary.get("overall", {})
    print(f"[rag] results -> {config.RAG_RESULTS_JSON}")
    print(f"[rag] report  -> {config.RAG_COMPARISON_MD}")
    print(
        f"[rag] hit@k={overall.get('hit_at_k')} "
        f"recall@k={overall.get('recall_at_k')} "
        f"citation={overall.get('citation_rate')} "
        f"faithfulness={overall.get('faithfulness_proxy')}"
    )
    return payload


if __name__ == "__main__":
    run()
