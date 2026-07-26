# Sample reports

Snapshots from a local `python run_demo.py` run (seed=42, 500 rows, offline
rule-based CoT fallback — Ollama optional).

| File | Description |
|---|---|
| `dev_analytics_report.md` | Developer + analytics report (provenance, step validation, prompt lift) |
| `analytics_report.html` | Visual analytics / AI-evaluation report |
| `anomaly_report.md` | Supervisor-facing XAI anomaly explanations |
| `rag_comparison_report.md` | Multi-retriever × multi-model RAG comparison |
| `audit_report.md` | Per-step explainability audit (detector / LLM / RAG) |

Regenerate locally with `make demo`, `make rag`, `make audit`, then copy from `data/reports/`.
