"""Mock Fusion Metadata Registry (FMR).

Mirrors the real FMR REST surface (a subset):

  * Structural metadata via the SDMX REST API
        GET /ws/public/sdmxapi/rest/structure/datastructure/{agency}/{id}/{version}
  * Data validation via FMR's data-processing web service
        POST /ws/public/data/validate      (accepts SDMX-CSV or SDMX-JSON)
  * Product info
        GET /ws/public/sdmxapi/rest/product

Run standalone:
    uvicorn metadata_registry.fmr_mock_api:app --reload --port 8000
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from metadata_registry import sdmx_csv  # noqa: E402
from metadata_registry.validator import validate_dataset  # noqa: E402

app = FastAPI(
    title="Mock Fusion Metadata Registry (FMR)",
    description="SDMX structural metadata + data validation for a banking dataflow.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "dataflow": config.DATAFLOW_REF}


@app.get("/ws/public/sdmxapi/rest/product")
def product() -> dict:
    return {
        "name": "Mock Fusion Metadata Registry",
        "version": app.version,
        "sdmxApi": "2.1",
    }


@app.get(
    "/ws/public/sdmxapi/rest/structure/datastructure/{agency}/{dsd_id}/{version}"
)
def datastructure(agency: str, dsd_id: str, version: str) -> dict:
    """Return the DSD as a (simplified) SDMX structure message."""
    if (agency, dsd_id, version) != (config.AGENCY_ID, config.DSD_ID, config.DSD_VERSION):
        raise HTTPException(status_code=404, detail="structure not found")
    return {
        "data": {
            "dataStructures": [
                {
                    "id": config.DSD_ID,
                    "agencyID": config.AGENCY_ID,
                    "version": config.DSD_VERSION,
                    "urn": config.DSD_URN,
                    "dataStructureComponents": {
                        "dimensionList": [
                            {"id": d, "codelist": (config.CODELISTS.get(d) and
                                                   f"{config.AGENCY_ID}:CL_{d}(1.0)")}
                            for d in config.DIMENSIONS
                        ],
                        "measure": config.MEASURE,
                        "attributeList": config.ATTRIBUTES,
                        "timeDimension": config.TIME_DIMENSION,
                    },
                }
            ]
        }
    }


async def _read_dataset(request: Request) -> list[dict]:
    """Accept SDMX-CSV (text/csv) or SDMX-JSON (application/json)."""
    content_type = request.headers.get("content-type", "")
    body = (await request.body()).decode("utf-8")
    if "json" in content_type:
        import json

        payload = json.loads(body)
        records = payload if isinstance(payload, list) else payload.get("records", [])
        return records
    # default: treat as SDMX-CSV
    if not body.strip():
        raise HTTPException(status_code=400, detail="empty dataset")
    try:
        return sdmx_csv.parse_csv_string(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"unreadable dataset: {exc}")


@app.post("/ws/public/data/validate")
async def validate(request: Request) -> dict:
    """FMR synchronous data-validation web service."""
    records = await _read_dataset(request)
    return validate_dataset(records)
