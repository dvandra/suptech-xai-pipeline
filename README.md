# SupTech-XAI: Metadata-Driven Anomaly Detection Pipeline

An end-to-end, on-prem **SupTech / RegTech** pipeline for a central-banking
context. It ingests high-frequency banking submissions, enforces **SDMX**
governance via a mock **Fusion Metadata Registry (FMR)**, classifies
unstructured text with local embeddings, explains outliers with a local LLM,
evaluates model quality, explores **RAG × multi-model** Q&A for supervisory /
risk / treasury use cases, and writes a **per-step audit trail** — all with
**no data leaving the machine**.

> **Note:** Independent educational simulation. Uses only synthetic data and
> mock services. Not affiliated with or endorsed by any central bank or
> supervisory authority.

---

## Capabilities at a glance

| # | Capability | What it does |
|---|---|---|
| 0 | **Synthetic SDMX data** | Generates banking submissions with seeded structural errors + semantic anomalies (ground truth for eval) |
| 1 | **SDMX / FMR governance** | Validates SDMX-CSV/JSON against a versioned DSD; rejects bad codes, missing dims, non-numeric measures, duplicates |
| 2 | **DuckDB wrangling** | Cleans, dedupes, builds SDMX series-key identity → Parquet |
| 3 | **Embedding classification** | Local MiniLM (or hashing fallback) + FAISS/numpy nearest-centroid anomaly scores |
| 4 | **LLM explainable AI** | Chain-of-Thought STEP1–STEP4 risk ratings via Ollama / rule-based fallback |
| 5 | **Analytics & AI evaluation** | Supervisory KPIs, detector P/R/F1 + threshold sweep, LLM faithfulness/judge, PSI drift, REST API + Streamlit + HTML/MD reports |
| 6 | **RAG exploration** | Dense / hybrid / filtered / corrective / graph retrievers × `llama3` / `mistral` / `qwen2.5` on supervisory, risk, treasury tracks |
| 7 | **Explainability audit trail** | Per-step reasoning + named validation checks for detector, LLM CoT, and RAG retrieve/generate — extensible for future pipelines |

**Also included:** Kafka (KRaft) streaming path · Podman/Compose local infra ·
OpenShift-ready image + manifests · offline fallbacks for every heavy dependency.

### Sample reports (checked in)

| Report | Link |
|---|---|
| Developer + analytics | [`docs/sample_reports/dev_analytics_report.md`](docs/sample_reports/dev_analytics_report.md) |
| Analytics HTML | [`docs/sample_reports/analytics_report.html`](docs/sample_reports/analytics_report.html) |
| Anomaly / XAI | [`docs/sample_reports/anomaly_report.md`](docs/sample_reports/anomaly_report.md) |
| RAG comparison | [`docs/sample_reports/rag_comparison_report.md`](docs/sample_reports/rag_comparison_report.md) |
| Audit / explainability | [`docs/sample_reports/audit_report.md`](docs/sample_reports/audit_report.md) |

### Documentation

| Doc | Topic |
|---|---|
| [`docs/README.md`](docs/README.md) | Documentation index |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full design & stage-by-stage architecture |
| [`docs/LLM_AND_DATA.md`](docs/LLM_AND_DATA.md) | Dataset, models, CoT validation |
| [`docs/RAG_AND_MODELS.md`](docs/RAG_AND_MODELS.md) | RAG variants & multi-model matrix |
| [`docs/AUDIT_AND_XAI.md`](docs/AUDIT_AND_XAI.md) | Per-step audit schema & validators |
| [`openshift/README.md`](openshift/README.md) | OpenShift deploy guide |

---

## Why this design

- **Governance first.** AI only sees data that already passed SDMX/FMR validation.
- **Embeddings before LLMs.** Bulk classify with vectors; escalate only outliers to an LLM.
- **Explainable, not black-box.** Every flag gets a structured Chain-of-Thought rationale + risk rating.
- **Evaluate & monitor.** Honest P/R/F1, faithfulness, LLM-as-judge, PSI drift — not “run and hope.”
- **Ground LLMs in documents (RAG).** Cited answers over synthetic policy / risk / treasury briefs.
- **Audit every AI step.** Reasoning steps + named checks, replayable without re-running models.
- **On-prem / air-gapped friendly.** Local embeddings, optional Ollama, fallbacks when deps are missing.

---

## Architecture

![Architecture](docs/images/architecture.svg)

<details>
<summary>ASCII overview (stages 0–7)</summary>

```
data_generator ──► Kafka or SDMX-CSV
                         │
                         ▼
              ┌── 1. FMR / SDMX validate ──┐
              │    reject non-compliant    │
              └────────────┬───────────────┘
                           ▼
              2. DuckDB wrangle → Parquet
                           ▼
              3. Embed + classify + score
                           ▼
              4. LLM CoT explain (XAI)
                           ▼
              5. Analytics + AI evaluation ──► API / dashboard / HTML+MD
                           │
              6. RAG (optional) ──► comparison report
                           │
              7. Audit trail (optional) ──► audit_trail.jsonl + report
```

</details>

---

## Technology stack

| Concern | Tool |
|---|---|
| Ingestion / streaming | Apache Kafka (KRaft), or local SDMX-CSV |
| Metadata governance | FastAPI mock **FMR** + **SDMX** DSD |
| Wrangling | **DuckDB** |
| Classification | HuggingFace `all-MiniLM-L6-v2` + **FAISS** (numpy fallback) |
| Explainable AI | **LangChain** + **Ollama** (rule-based CoT fallback) |
| Analytics & eval | DuckDB KPIs, P/R/F1, PSI, FastAPI, **Streamlit**, HTML/MD reports |
| RAG | Dense / hybrid / filtered / corrective / graph + multi-model matrix |
| Audit / XAI trail | Versioned `AuditEvent` schema + pluggable validators |
| Containers | **Podman** (default) + Compose; Docker-compatible |
| Orchestration | **OpenShift** manifests (restricted SCC) |

### Offline by design

| Optional component | Fallback |
|---|---|
| Kafka | local SDMX-CSV / JSONL |
| FMR HTTP API | in-process validator (same logic) |
| sentence-transformers | hashing vectoriser (numpy) |
| FAISS | numpy nearest-centroid |
| Ollama (Stage 4) | rule-based CoT explainer |
| Ollama (judge) | deterministic rubric scorer |
| Ollama (Stage 6 RAG) | grounded answer with chunk-ID citations |
| Streamlit | static HTML analytics report |

---

## Quickstart

No containers, Kafka, or LLM required for the core demo:

```bash
make install                              # .venv + core deps
make demo                                 # stages 0–5
make rag                                  # stage 6
make audit                                # stage 7
# one shot:
python run_demo.py --count 500 --with-rag --with-audit
```

Example output:

```
=== Stage 1: ingest & FMR validation ===
[ingest] accepted≈433 rejected≈67
=== Stage 3: embed, classify & score anomalies ===
[embed] flagged≈29
=== Stage 4: Chain-of-Thought explanations ===
[explain] step-pass=29/29
=== Stage 5: analytics & AI evaluation ===
[analytics] detector P/R/F1 + LLM validity/faithfulness/judge
=== Stage 6: RAG & multi-model exploration ===
[rag] hit@k≈0.91 faithfulness≈0.88
=== Stage 7: explainability & audit trail ===
[audit] events≈328 pass_rate≈0.93
```

Outputs under `data/` and `data/reports/` (JSON metrics, anomaly report,
analytics HTML/MD, RAG comparison, audit trail).

---

## SDMX & FMR fidelity

The AI never runs on structurally invalid data. The mock mirrors real FMR
concepts:

| Real concept | In this project |
|---|---|
| Versioned **DSD** | `DEMO:BANKING_FLOWS(1.0)` |
| **Dataflow** + URN | `DEMO:BANKING_FLOWS_FLOW(1.0)` |
| **SDMX-CSV** | `data/raw_submissions.csv` |
| **SDMX-JSON** stream | Kafka payloads |
| Structure query | `GET .../structure/datastructure/{agency}/{id}/{version}` |
| Data validation | `POST /ws/public/data/validate` |
| Validation report | Position-indexed errors, severity, codes |
| Series key identity | `ref_area.institution_id.asset_class.time_period` |

Checks: mandatory dimensions, codelists, numeric measure, `TIME_PERIOD` format,
duplicate observations.

```bash
curl localhost:8000/ws/public/sdmxapi/rest/structure/datastructure/DEMO/BANKING_FLOWS/1.0
curl -X POST localhost:8000/ws/public/data/validate \
     -H 'Content-Type: text/csv' --data-binary @data/raw_submissions.csv
```

---

## Stage details

### Stages 0–4 — ingest → classify → explain

```bash
python data_generator/kafka_producer.py --local --count 500
python pipeline/1_ingest_validate.py
python pipeline/2_wrangle_duckdb.py
python pipeline/3_embed_classify.py
python pipeline/4_explain_anomaly.py
```

Stage 4 uses a labelled **STEP1–STEP4** CoT contract (purpose vs asset → amount →
red flags → rating/action). See [`docs/LLM_AND_DATA.md`](docs/LLM_AND_DATA.md).

### Stage 5 — analytics & AI evaluation

- Supervisory KPIs (anomaly rate, flagged value by jurisdiction/asset/institution)
- Detector P/R/F1 + confusion matrix + F1-optimal threshold sweep
- LLM validity, faithfulness, LLM-as-judge (1–5)
- PSI drift bands (`stable` / `moderate` / `major`)
- REST API (`make api`), Streamlit (`make dashboard`), HTML + developer MD reports

```bash
python analytics/run_analytics.py
make api          # :8001  /metrics/summary|evaluation|drift|all
make dashboard    # Streamlit
```

### Stage 6 — RAG exploration

| Retrievers | dense · hybrid · filtered · corrective · graph |
|---|---|
| Models | `llama3` · `mistral` · `qwen2.5` |
| Tracks | supervisory · risk narrative · treasury / liquidity |
| Metrics | Hit@k, recall@k, citation rate, term coverage, faithfulness proxy |

```bash
make rag
# → data/rag_results.json + data/reports/rag_comparison_report.md
```

Details: [`docs/RAG_AND_MODELS.md`](docs/RAG_AND_MODELS.md).

### Stage 7 — explainability & audit

Structured trail for detector, LLM CoT, and RAG retrieve/generate:

```bash
make audit
# → data/audit_trail.jsonl + data/audit_summary.json + data/reports/audit_report.md
```

| Pipeline | Checks |
|---|---|
| `detector` | Score / category present |
| `llm_xai` | STEP1–STEP4 contract + parseable rating |
| `rag` | Hit@k, citations, faithfulness gate |

Extend future use cases by registering a validator in `audit/validators.py`.  
Details: [`docs/AUDIT_AND_XAI.md`](docs/AUDIT_AND_XAI.md).

---

## Optional: Kafka + FMR containers

```bash
make infra-up                 # Podman Compose (or CONTAINER_ENGINE=docker)
python data_generator/kafka_producer.py --count 5000
python pipeline/1_ingest_validate.py --source kafka
make infra-down
```

For live embeddings / LLMs, uncomment optional blocks in `requirements.txt` and:

```bash
ollama pull llama3
ollama pull mistral
ollama pull qwen2.5
```

---

## Deploy on OpenShift

OpenShift-native manifests in [`openshift/`](openshift/): ImageStream +
BuildConfig, FMR / metrics API / dashboard Deployments + Routes, ephemeral
Kafka, pipeline CronJob. Single restricted-SCC-compatible image.

```bash
oc new-project suptech-xai
make oc-build
make oc-deploy
oc get route dashboard metrics-api fmr
```

See [`openshift/README.md`](openshift/README.md).

---

## Repository layout

```
suptech-xai-pipeline/
├── config.py                     # DSD, paths, RAG/audit/LLM settings
├── compose.yaml                  # Kafka (KRaft) + FMR mock
├── run_demo.py                   # end-to-end orchestrator (--with-rag/--with-audit)
├── Containerfile                 # unified app image
├── data_generator/               # synthetic SDMX submissions
├── metadata_registry/            # FMR mock + SDMX-CSV + validator
├── pipeline/                     # stages 1–4
├── analytics/                    # stage 5 — KPIs, eval, drift, reports, API
├── dashboard/                    # Streamlit UI
├── rag/                          # stage 6 — corpus, retrievers, multi-model runner
├── audit/                        # stage 7 — schema, tracers, validators, report
├── docs/                         # architecture, LLM/RAG/audit guides, samples
└── openshift/                    # ImageStream, BuildConfig, Deployments, CronJob
```

---

## License

MIT — see `LICENSE`. Synthetic data only; educational simulation.
