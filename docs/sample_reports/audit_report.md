# SupTech-XAI — Explainability & Audit Report

_Generated 2026-07-26 06:18 UTC_

Per-step audit of detector decisions, LLM Chain-of-Thought explanations, and RAG retrieve/generate stages. Each event carries reasoning steps and validation checks for independent review.

See [`docs/AUDIT_AND_XAI.md`](../AUDIT_AND_XAI.md).

## Run summary

| Item | Value |
|---|---|
| Run id | `ae23d19eb250` |
| Schema | `1.0` |
| Events | 328 |
| Passed | 304 |
| Failed | 24 |
| Pass rate | 0.9268 |

### By pipeline

| Pipeline | n | ok | failed |
|---|---|---|---|
| detector | 29 | 29 | 0 |
| llm_xai | 29 | 29 | 0 |
| rag | 270 | 246 | 24 |

### By stage

| Stage | n | ok | failed |
|---|---|---|---|
| stage3_classify | 29 | 29 | 0 |
| stage4_explain | 29 | 29 | 0 |
| stage6_rag_retrieve | 135 | 123 | 12 |
| stage6_rag_generate | 135 | 123 | 12 |

### Source coverage

| Source | Count |
|---|---|
| detector | 29 |
| llm_xai | 29 |
| rag_cases | 135 |

## Failures (sample)

- `SUP-2:dense:llama3` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:dense:llama3` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:dense:mistral` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:dense:mistral` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:dense:qwen2.5` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:dense:qwen2.5` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:hybrid:llama3` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:hybrid:llama3` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:hybrid:mistral` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:hybrid:mistral` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:hybrid:qwen2.5` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:hybrid:qwen2.5` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:corrective:llama3` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k
- `SUP-2:corrective:llama3` · rag/stage6_rag_generate · failed=rag_faithfulness_proxy_gate
- `SUP-2:corrective:mistral` · rag/stage6_rag_retrieve · failed=rag_retrieve_hit_at_k

## Example audited steps

### `SUP-2:dense:llama3` — rag/retrieve

- status: **failed** · model=`llama3` · engine=`dense`
- reasoning:
  - **retrieve** Retriever=dense: top_k ids=['RISK-CONC-010', 'TRY-RATE-022', 'TRY-LIQ-020', 'TRY-FX-021']
- validations:
  - [PASS] `rag_retrieve_nonempty` — Retrieved at least one chunk
  - [FAIL] `rag_retrieve_hit_at_k` — Hit@k against gold chunk ids (score=0.0)

### `SUP-2:dense:llama3` — rag/generate

- status: **failed** · model=`llama3` · engine=`rule-based`
- reasoning:
  - **generate** Model=llama3 engine=rule-based: TRACK: supervisory QUESTION: Purpose text cites a sanctioned counterparty via an intermediary. How should supervisors rate and escalate this? ANSWER: Based on r
- validations:
  - [PASS] `rag_answer_nonempty` — Answer text non-empty
  - [PASS] `rag_citation_present` — At least one retrieved chunk cited (score=0.75)
  - [PASS] `rag_term_coverage` — Required domain terms covered (score=1.0)
  - [FAIL] `rag_faithfulness_proxy_gate` — Faithfulness proxy >= 0.5 (score=0.425)

### `GB.BANK033.LOAN.2024-08` — detector/anomaly_decision

- status: **ok** · model=`None` · engine=`embeddings`
- reasoning:
  - **score** Anomaly score vs threshold decision: score=1.0801 category=LOAN is_anomaly=True
- validations:
  - [PASS] `detector_score_present` — Anomaly score present
  - [PASS] `detector_category_present` — Predicted category present

### `CH.BANK038.FX.2025-01` — detector/anomaly_decision

- status: **ok** · model=`None` · engine=`embeddings`
- reasoning:
  - **score** Anomaly score vs threshold decision: score=1.0801 category=LOAN is_anomaly=True
- validations:
  - [PASS] `detector_score_present` — Anomaly score present
  - [PASS] `detector_category_present` — Predicted category present

### `CH.BANK012.FX.2025-06` — detector/anomaly_decision

- status: **ok** · model=`None` · engine=`embeddings`
- reasoning:
  - **score** Anomaly score vs threshold decision: score=1.0803 category=DEPOSIT is_anomaly=True
- validations:
  - [PASS] `detector_score_present` — Anomaly score present
  - [PASS] `detector_category_present` — Predicted category present

## Artefacts

- Audit trail JSONL: `data/audit_trail.jsonl`
- Audit summary JSON: `data/audit_summary.json`
- This report: `data/reports/audit_report.md`

## Extending for future use cases

1. Add a validator function in `audit/validators.py`.
2. Register it on `VALIDATORS` under a new pipeline key.
3. Emit events via `AuditTracer.step(...)` or `audit.build` helpers.
4. Re-run `python -m audit.run_audit` — report format stays stable.

---

_Synthetic data only · educational simulation._
