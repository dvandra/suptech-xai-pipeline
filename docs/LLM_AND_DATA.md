# Dataset, models & LLM use cases

This document is the source of truth for **what data** the pipeline uses,
**which models** run where, and **how LLMs are applied, validated, and
improved**.


---

## 1. Dataset

### What it is
A **synthetic SDMX banking submissions** dataset, generated locally by
`data_generator/kafka_producer.py`. No real bank or supervisory data is used.

### Why synthetic
Supervisory data is confidential. A seeded generator gives:

- reproducible runs (`--seed`, default `42`)
- known **ground-truth** outliers (for honest precision / recall / F1)
- controllable structural errors (for FMR validation demos)

### Schema (SDMX Data Structure Definition)
Agency / artefacts (see `config.py`):

| Artefact | Value |
|---|---|
| Agency | `DEMO` |
| DSD | `DEMO:BANKING_FLOWS(1.0)` |
| Dataflow | `DEMO:BANKING_FLOWS_FLOW(1.0)` |

| Role | Columns |
|---|---|
| Dimensions | `REF_AREA`, `INSTITUTION_ID`, `ASSET_CLASS`, `TIME_PERIOD` |
| Measure | `OBS_VALUE` |
| Attributes | `CURRENCY`, `TXN_PURPOSE` (free text — the AI input) |

Exchange formats:

- **SDMX-CSV** → `data/raw_submissions.csv` (local path)
- **SDMX-JSON** → Kafka messages (optional infra path)

### Default generation parameters

| Parameter | Default | Meaning |
|---|---|---|
| `--count` | `500` | total rows |
| `--invalid-rate` | `0.12` | structural violations (FMR should reject) |
| `--anomaly-rate` | `0.06` | semantic outliers (AI should flag) |
| `--seed` | `42` | reproducibility |

Rough expected mix: ~60 invalid, ~30 anomalous purposes, ~410 “normal”
observations. After FMR, ~440 rows typically enter analytics.

### Ground truth for AI evaluation
Anomalous rows are seeded with purposes from a fixed list
(`ANOMALOUS_PURPOSES` in the generator), e.g. sanctions / structuring /
layering language, often with extreme amounts (`5e7`–`5e8`).

Evaluation reconstructs labels by matching `txn_purpose` against that list
(`analytics/evaluation.py`). Detector predictions come from stage 3
(`is_anomaly`).

### Normal vs anomalous text (examples)

**Normal** (per asset class centroids): mortgage origination, bond settlement,
IRS fixed-leg payment, spot FX, etc.

**Anomalous** (fixed list): offshore shell transfers, structuring below
thresholds, sanctioned counterparties, layering / round-trips, trade
mis-invoicing.

---

## 2. Models (non-LLM and LLM)

| Stage | Model / engine | Default | Role |
|---|---|---|---|
| 3 — classify | HuggingFace **`all-MiniLM-L6-v2`** (+ FAISS) | local | Embed `TXN_PURPOSE`, nearest-centroid category, anomaly score |
| 3 — fallback | Hashing vectoriser + numpy | if MiniLM/FAISS absent | Same API, deterministic offline |
| 4 — explain | **Ollama `llama3`** via LangChain | `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | Chain-of-Thought risk rationale for flagged rows only |
| 4 — fallback | Rule-based CoT | if Ollama down | Same 4-step structure, keyword + amount rules |
| 5 — judge | Same Ollama model (or rule rubric) | optional override `OLLAMA_JUDGE_MODEL` | Score explanations 1–5 |

Environment overrides:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export OLLAMA_JUDGE_MODEL=llama3   # optional; defaults to OLLAMA_MODEL
export ANOMALY_SIGMA=1.5
```

**Design rule:** embeddings classify *everything*; the LLM sees only outliers.
That keeps cost/latency low and matches an on-prem / air-gapped posture.

---

## 3. LLM use cases (detailed)

### Use case A — Explainable anomaly justification (Stage 4)
**Goal.** Give a supervisor an auditable, human-readable reason a submission
was flagged — not just a distance score.

**Input.** One flagged observation: series id, jurisdiction, institution,
asset class, period, amount/currency, purpose text, predicted category,
anomaly score.

**Prompt contract (v2 — structured CoT).** The model must answer in **four
labelled steps**:

1. **STEP1 — Purpose vs asset class** — consistency check  
2. **STEP2 — Amount plausibility** — magnitude relative to activity type  
3. **STEP3 — Red-flag language** — cite terms actually present in the purpose  
4. **STEP4 — Rating & action** — end with `LOW` / `MEDIUM` / `HIGH` and a
   recommended supervisory action  

**Output artefacts.**

- `data/reports/anomaly_report.md` — human compliance report  
- `data/explanations.jsonl` — structured rows (`risk_rating`, `steps`,
  `prompt_version`, `engine`, …) for evaluation  

### Use case B — LLM-as-judge (Stage 5 evaluation)
**Goal.** Score each explanation 1–5 for correctness, evidence use, and
clarity for a human supervisor.

**Offline path.** If Ollama is unavailable, a deterministic rubric scores the
same dimensions (rating present, red-flag grounding, amount reference,
structured steps) so CI still runs.

### What the LLM is *not* used for
- Bulk classification of every row (that is MiniLM / FAISS)  
- Structural SDMX validation (that is the FMR)  
- Replacing human supervisory decisions  

---

## 4. Step-by-step validation & improvement loop

Validation is layered so each CoT step can fail independently:

| Check | What “good” means |
|---|---|
| **Format** | All four `STEP1`…`STEP4` (or `1.`…`4.`) sections present |
| **STEP1** | Mentions asset class and/or purpose/category language |
| **STEP2** | Mentions amount / currency / magnitude |
| **STEP3** | If the purpose contains red-flag terms, at least one is cited |
| **STEP4** | Ends with a parseable `LOW` / `MEDIUM` / `HIGH` rating |
| **Faithfulness** | Aggregate recall of red-flag terms across explanations |
| **Judge** | Mean 1–5 score (LLM or rubric) |

**Improvement path encoded in the repo:**

1. **v1 prompt** — free-form “reason step by step” (legacy behaviour)  
2. **v2 prompt** — labelled `STEPn:` contract (current default)  
3. Metrics compare structure compliance / step pass rates / judge score  
4. Failures are listed in the **developer report** for prompt iteration  

Tune detector threshold via `threshold_sweep` (F1-optimal σ) and LLM quality
via prompt version + judge averages — both appear in the analytics / dev
reports.

---

## 5. Reports produced

| Report | Path | Audience |
|---|---|---|
| Anomaly / XAI | `data/reports/anomaly_report.md` | Supervisors |
| Analytics (HTML) | `data/reports/analytics_report.html` | Analytics / model risk |
| Developer + analytics | `data/reports/dev_analytics_report.md` | Engineers iterating on LLM quality |
| Metrics (JSON) | `data/metrics.json` | API / CI |
| Sample snapshot (tracked) | `docs/sample_reports/` | Readers on GitHub without running the demo |

Regenerate everything:

```bash
python run_demo.py
# or
make demo
```

For Stage 6 RAG exploration (retrievers × models):

```bash
make rag
# or
python run_demo.py --with-rag
```

See also [`RAG_AND_MODELS.md`](RAG_AND_MODELS.md).

---

## 6. Quick map to code

| Concern | Module |
|---|---|
| Dataset generation | `data_generator/kafka_producer.py` |
| DSD / paths / models | `config.py` |
| Embeddings + anomaly score | `pipeline/3_embed_classify.py`, `pipeline/embeddings.py` |
| LLM explain (CoT) | `pipeline/4_explain_anomaly.py` |
| Detector + LLM eval | `analytics/evaluation.py` |
| Dev + analytics reports | `analytics/report.py`, `analytics/dev_report.py` |
| Orchestration | `run_demo.py`, `analytics/run_analytics.py` |
