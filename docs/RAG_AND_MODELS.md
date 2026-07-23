# RAG variants & LLM models for financial analytics

This document describes Stage 6 of the project: exploring **retrieval-augmented
generation (RAG)** patterns and **local LLMs** for supervisory analysis, risk
narratives, and treasury / liquidity Q&A.

Synthetic corpus and questions only. Educational simulation — not affiliated
with or endorsed by any central bank or supervisory authority.

---

## Why RAG here

Tabular SDMX validation + embedding anomaly detection (Stages 1–5) answers
*what* is anomalous. RAG answers *why it matters* by grounding an LLM in
policy, typology, risk, and treasury briefs — with **citations**, so outputs
are auditable.

Design constraints:

- On-prem friendly (local embeddings + optional Ollama)
- Offline fallbacks (hashing embedder + rule-based answers)
- No external document stores required

---

## Corpus

Nine markdown documents under `rag/corpus/` with front-matter metadata
(`track`, `topics`, `asset_classes`, `jurisdictions`):

| Track | Docs | Themes |
|---|---|---|
| Supervisory | AML structuring/layering, sanctions/shell, SDMX data quality | Typology + governance |
| Risk | Concentration/PSI, risk-score drivers, trade mis-invoicing | Risk narrative / prediction *assist* |
| Treasury | Liquidity buffers & roll risk, FX mismatch, rate-sensitive positions | Liquidity / FX / rates |

Risk-prediction here means **driver explanation** of elevated scores — not a
black-box market forecast.

---

## Retrievers compared

| Retriever | Idea | Finance fit |
|---|---|---|
| **dense** | Embedding similarity (MiniLM or hashing fallback) | Baseline semantic search |
| **hybrid** | Dense + BM25 via reciprocal rank fusion | Exact terms (PSI, ISIN-like codes, typology words) |
| **filtered** | Dense pool + metadata filters (asset class, jurisdiction, track) | SDMX-aligned retrieval |
| **corrective** | Hybrid retrieve → coverage check → expanded re-query | Reduces empty/weak context |
| **graph** | Topic/asset/jurisdiction graph neighbourhood + dense re-rank | Linked entity reasoning |

Configured via `RAG_RETRIEVERS` (default: all five).

---

## LLMs compared

Default matrix (`RAG_MODELS`):

| Model tag | Role |
|---|---|
| `llama3` | General on-prem explainer (default elsewhere in the repo) |
| `mistral` | Alternative instruction-tuned local model |
| `qwen2.5` | Third local option for sensitivity checks |

If Ollama is unavailable, answers use a **deterministic grounded fallback** that
still cites retrieved chunk IDs — so evaluation runs in CI.

Embeddings: `all-MiniLM-L6-v2` when installed; else hashing vectoriser.

---

## Question tracks

1. **Supervisory analysis** — typology, sanctions, why FMR-before-AI matters  
2. **Risk narrative** — PSI/concentration, score drivers, trade mis-invoicing  
3. **Treasury / liquidity** — buffers, roll risk, FX mismatch, rate activity  

Each case has gold chunk IDs and required terms for automated scoring.

---

## Metrics

| Metric | Meaning |
|---|---|
| Hit@k | ≥1 gold chunk in top-k |
| Recall@k | Fraction of gold chunks retrieved |
| Citation rate | Retrieved IDs mentioned in the answer |
| Term coverage | Required domain terms present in the answer |
| Faithfulness proxy | Weighted blend of the above |

---

## How to run

```bash
make rag
# or
python -m rag.run_rag
```

Outputs:

- `data/rag_results.json`
- `data/reports/rag_comparison_report.md`
- Sample snapshot: `docs/sample_reports/rag_comparison_report.md`

Environment knobs:

```bash
export RAG_MODELS=llama3,mistral,qwen2.5
export RAG_RETRIEVERS=dense,hybrid,filtered,corrective,graph
export RAG_TOP_K=4
export OLLAMA_BASE_URL=http://localhost:11434
```

---

## Map to code

| Piece | Path |
|---|---|
| Corpus | `rag/corpus/*.md` |
| Index + BM25 | `rag/index.py` |
| Retrievers | `rag/retrievers/__init__.py` |
| Cases / runners | `rag/pipelines/__init__.py` |
| Eval | `rag/evaluate_rag.py` |
| Orchestrator | `rag/run_rag.py` |
| Report | `rag/report.py` |
