# Documentation index

Educational simulation. Synthetic data only. Not affiliated with or endorsed
by any central bank or supervisory authority.

| Document | What it covers |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | End-to-end design, stages 0–6, offline, deployment |
| [`LLM_AND_DATA.md`](LLM_AND_DATA.md) | Dataset shape, embedding/LLM defaults, CoT validation |
| [`RAG_AND_MODELS.md`](RAG_AND_MODELS.md) | RAG variants, multi-model matrix, finance tracks, metrics |
| [`sample_reports/`](sample_reports/) | Checked-in demo report snapshots (analytics + RAG) |
| [`diagrams/`](diagrams/) | Mermaid sources (`.mmd`) for architecture diagrams |
| [`images/`](images/) | Rendered SVG diagrams used by the README |

## Quick links (run locally)

```bash
make demo                 # Stages 0–5
make rag                  # Stage 6 RAG comparison
python run_demo.py --with-rag   # full demo including Stage 6
```

## Documentation map

```
Stages 0–1  SDMX / FMR governance     → ARCHITECTURE §4–6, README “SDMX & FMR”
Stages 3–4  Embeddings + CoT XAI      → LLM_AND_DATA.md
Stage 5     Eval / drift / reports    → LLM_AND_DATA.md, sample_reports/
Stage 6     RAG × models × tracks     → RAG_AND_MODELS.md, sample_reports/
```
