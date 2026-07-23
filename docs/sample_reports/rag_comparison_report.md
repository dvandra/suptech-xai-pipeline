# SupTech-XAI — RAG & LLM Comparison Report

_Generated 2026-07-23 18:56 UTC_

Compares **dense**, **hybrid**, **metadata-filtered**, **corrective**, and **graph** retrievers across **supervisory analysis**, **risk narrative**, and **treasury / liquidity** question tracks. Synthetic corpus only.

See [`docs/RAG_AND_MODELS.md`](../RAG_AND_MODELS.md).

## Run config

| Item | Value |
|---|---|
| Retrievers | dense, hybrid, filtered, corrective, graph |
| Models | llama3, mistral, qwen2.5 |
| Top-k | 4 |
| Embedder | `hashing-256d (offline fallback)` |
| Corpus docs | 9 |

## Overall metrics

| Metric | Value |
|---|---|
| n (case × retriever × model) | 135 |
| Hit@k | 0.9111 |
| Recall@k | 0.9111 |
| Citation rate | 0.75 |
| Term coverage | 0.9778 |
| Faithfulness proxy | 0.8761 |

## By retriever

| Retriever | Hit@k | Recall@k | Citation | Faithfulness | n |
|---|---|---|---|---|---|
| dense | 0.8889 | 0.8889 | 0.75 | 0.8694 | 27 |
| hybrid | 0.8889 | 0.8889 | 0.75 | 0.8583 | 27 |
| filtered | 1.0 | 1.0 | 0.75 | 0.925 | 27 |
| corrective | 0.8889 | 0.8889 | 0.75 | 0.8583 | 27 |
| graph | 0.8889 | 0.8889 | 0.75 | 0.8694 | 27 |

## By model

| Model | Hit@k | Recall@k | Citation | Faithfulness | n |
|---|---|---|---|---|---|
| llama3 | 0.9111 | 0.9111 | 0.75 | 0.8761 | 45 |
| mistral | 0.9111 | 0.9111 | 0.75 | 0.8761 | 45 |
| qwen2.5 | 0.9111 | 0.9111 | 0.75 | 0.8761 | 45 |

## By track

| Track | Hit@k | Recall@k | Citation | Faithfulness | n |
|---|---|---|---|---|---|
| supervisory | 0.7333 | 0.7333 | 0.75 | 0.7783 | 45 |
| risk | 1.0 | 1.0 | 0.75 | 0.925 | 45 |
| treasury | 1.0 | 1.0 | 0.75 | 0.925 | 45 |

## Strongest runs (sample)

- `SUP-1` / dense / llama3 faithfulness=0.925 retrieved=['POL-AML-001', 'RISK-CONC-010', 'RISK-PRED-011', 'POL-SDMX-003']
- `SUP-1` / dense / mistral faithfulness=0.925 retrieved=['POL-AML-001', 'RISK-CONC-010', 'RISK-PRED-011', 'POL-SDMX-003']
- `SUP-1` / dense / qwen2.5 faithfulness=0.925 retrieved=['POL-AML-001', 'RISK-CONC-010', 'RISK-PRED-011', 'POL-SDMX-003']
- `SUP-1` / hybrid / llama3 faithfulness=0.925 retrieved=['POL-AML-001', 'RISK-CONC-010', 'RISK-PRED-011', 'POL-SDMX-003']
- `SUP-1` / hybrid / mistral faithfulness=0.925 retrieved=['POL-AML-001', 'RISK-CONC-010', 'RISK-PRED-011', 'POL-SDMX-003']

## Weakest runs (sample)

- `SUP-2` / hybrid / llama3 faithfulness=0.325 retrieved=['TRY-RATE-022', 'RISK-CONC-010', 'POL-AML-001', 'RISK-PRED-011'] gold=['POL-SAN-002']
- `SUP-2` / hybrid / mistral faithfulness=0.325 retrieved=['TRY-RATE-022', 'RISK-CONC-010', 'POL-AML-001', 'RISK-PRED-011'] gold=['POL-SAN-002']
- `SUP-2` / hybrid / qwen2.5 faithfulness=0.325 retrieved=['TRY-RATE-022', 'RISK-CONC-010', 'POL-AML-001', 'RISK-PRED-011'] gold=['POL-SAN-002']
- `SUP-2` / corrective / llama3 faithfulness=0.325 retrieved=['TRY-RATE-022', 'RISK-CONC-010', 'POL-AML-001', 'RISK-PRED-011'] gold=['POL-SAN-002']
- `SUP-2` / corrective / mistral faithfulness=0.325 retrieved=['TRY-RATE-022', 'RISK-CONC-010', 'POL-AML-001', 'RISK-PRED-011'] gold=['POL-SAN-002']

## Artefacts

- Results JSON: `data/rag_results.json`
- This report: `data/reports/rag_comparison_report.md`

---

_Synthetic data only · educational simulation._
