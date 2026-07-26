"""Central configuration shared across the pipeline stages.

Values can be overridden via environment variables so the same code runs both
in the local demo (no external services) and against real infrastructure
(Kafka, an FMR server, Ollama).
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"

# Files used to hand data between stages in --local mode.
# Raw submissions are written as SDMX-CSV (a real SDMX exchange format that the
# FMR can validate directly); everything downstream is internal JSON/Parquet.
RAW_CSV = DATA_DIR / "raw_submissions.csv"
VALIDATED_JSONL = DATA_DIR / "validated_submissions.jsonl"
WRANGLED_PARQUET = DATA_DIR / "wrangled.parquet"
CLASSIFIED_JSONL = DATA_DIR / "classified.jsonl"
ANOMALY_REPORT = REPORTS_DIR / "anomaly_report.md"

# Stage 4 also emits a structured record of every explanation, which the
# analytics/evaluation layer consumes.
EXPLANATIONS_JSONL = DATA_DIR / "explanations.jsonl"

# Stage 5 (analytics) outputs.
METRICS_JSON = DATA_DIR / "metrics.json"
ANALYTICS_HTML = REPORTS_DIR / "analytics_report.html"
DEV_ANALYTICS_MD = REPORTS_DIR / "dev_analytics_report.md"

# --- Kafka -----------------------------------------------------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sdmx.banking.submissions")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "suptech-ingest")

# --- SDMX Data Structure Definition (the "schema" the FMR enforces) --------
# Modelled on real SDMX structural metadata: an agency maintains a versioned
# Data Structure Definition (DSD), referenced by a Dataflow. FMR validates
# incoming data against the Dataflow/DSD identified by its URN.
AGENCY_ID = "DEMO"
DSD_ID = "BANKING_FLOWS"
DSD_VERSION = "1.0"
DATAFLOW_ID = "BANKING_FLOWS_FLOW"
DATAFLOW_VERSION = "1.0"

# SDMX artefact identifiers (agency:id(version)) and canonical URNs.
DSD_REF = f"{AGENCY_ID}:{DSD_ID}({DSD_VERSION})"
DATAFLOW_REF = f"{AGENCY_ID}:{DATAFLOW_ID}({DATAFLOW_VERSION})"
DSD_URN = f"urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure={DSD_REF}"
DATAFLOW_URN = f"urn:sdmx:org.sdmx.infomodel.datastructure.Dataflow={DATAFLOW_REF}"

# Time dimension is special in SDMX (the dimension at observation level).
DIMENSIONS = ["REF_AREA", "INSTITUTION_ID", "ASSET_CLASS", "TIME_PERIOD"]
TIME_DIMENSION = "TIME_PERIOD"
MEASURE = "OBS_VALUE"
ATTRIBUTES = ["CURRENCY", "TXN_PURPOSE"]

# The ordered list of components as they appear in the SDMX-CSV data columns.
COMPONENTS = ["REF_AREA", "INSTITUTION_ID", "ASSET_CLASS", "TIME_PERIOD",
              "OBS_VALUE", "CURRENCY", "TXN_PURPOSE"]

# Codelists constrain the allowed values for coded dimensions/attributes.
CODELISTS = {
    "REF_AREA": ["US", "GB", "DE", "JP", "CH", "SG", "FR", "IN"],
    "ASSET_CLASS": ["LOAN", "DEPOSIT", "SECURITY", "DERIVATIVE", "FX"],
    "CURRENCY": ["USD", "EUR", "GBP", "JPY", "CHF", "SGD", "INR"],
}

# --- FMR (Fusion Metadata Registry mock) -----------------------------------
# Endpoints mirror the real FMR REST API:
#   * structural metadata via the SDMX REST API
#   * data validation via FMR's data-processing web service
FMR_BASE_URL = os.getenv("FMR_BASE_URL", "http://localhost:8000")
FMR_VALIDATE_ENDPOINT = f"{FMR_BASE_URL}/ws/public/data/validate"
FMR_STRUCTURE_ENDPOINT = (
    f"{FMR_BASE_URL}/ws/public/sdmxapi/rest/structure/datastructure/"
    f"{AGENCY_ID}/{DSD_ID}/{DSD_VERSION}"
)

# --- Financial-crime red-flag vocabulary -----------------------------------
# Used by the XAI explainer and by the evaluation harness (faithfulness /
# groundedness scoring of LLM explanations).
RED_FLAG_TERMS = [
    "sanction",
    "shell",
    "structuring",
    "threshold",
    "layering",
    "round-trip",
    "mis-invoic",
    "unregistered",
    "offshore",
]

# --- Anomaly detection -----------------------------------------------------
# Records whose distance-to-nearest-category-centroid exceeds
# (mean + ANOMALY_SIGMA * std) are flagged for XAI explanation.
ANOMALY_SIGMA = float(os.getenv("ANOMALY_SIGMA", "1.5"))

# --- Local LLM (Ollama) ----------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
# Optional separate judge model; defaults to the explainer model.
OLLAMA_JUDGE_MODEL = os.getenv("OLLAMA_JUDGE_MODEL", OLLAMA_MODEL)
# CoT prompt contract: v2 requires labelled STEP1..STEP4 blocks (see docs/LLM_AND_DATA.md).
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v2")

# --- RAG exploration (Stage 6) ---------------------------------------------
RAG_CORPUS_DIR = ROOT / "rag" / "corpus"
RAG_INDEX_DIR = DATA_DIR / "rag_index"
RAG_RESULTS_JSON = DATA_DIR / "rag_results.json"
RAG_COMPARISON_MD = REPORTS_DIR / "rag_comparison_report.md"
# Comma-separated Ollama model tags to compare (offline fallback skips real calls).
RAG_MODELS = [
    m.strip()
    for m in os.getenv("RAG_MODELS", "llama3,mistral,qwen2.5").split(",")
    if m.strip()
]
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_RETRIEVERS = [
    r.strip()
    for r in os.getenv(
        "RAG_RETRIEVERS", "dense,hybrid,filtered,corrective,graph"
    ).split(",")
    if r.strip()
]

# --- Audit / explainability trail (cross-cutting) --------------------------
AUDIT_JSONL = DATA_DIR / "audit_trail.jsonl"
AUDIT_SUMMARY_JSON = DATA_DIR / "audit_summary.json"
AUDIT_REPORT_MD = REPORTS_DIR / "audit_report.md"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
