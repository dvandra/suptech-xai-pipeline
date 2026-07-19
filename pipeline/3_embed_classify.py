"""Stage 3 - Embedding-based classification & anomaly scoring.

Bulk-classifies the unstructured ``TXN_PURPOSE`` text WITHOUT calling an LLM
per row - the scalable pattern used in central-bank SupTech for large
statistical datasets:

  1. Embed each record's purpose text with a local model.
  2. Build reference centroids for each asset-class category from labelled
     seed phrases and index them (FAISS if available, else numpy).
  3. Assign every record to its nearest category (vector similarity).
  4. Score anomalies by distance-to-nearest-centroid; flag records beyond
     ``mean + ANOMALY_SIGMA * std`` as outliers for downstream XAI review.

Only the small set of flagged outliers is later sent to the (expensive) LLM.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from data_generator.kafka_producer import NORMAL_PURPOSES  # noqa: E402
from pipeline.embeddings import get_embedder  # noqa: E402


def _build_centroids(embedder):
    """One centroid per asset-class, averaged over its labelled seed phrases."""
    categories, centroids = [], []
    for category, phrases in NORMAL_PURPOSES.items():
        vecs = embedder.encode(phrases)
        centroids.append(vecs.mean(axis=0))
        categories.append(category)
    return categories, np.vstack(centroids).astype(np.float32)


class _CentroidIndex:
    """Nearest-centroid search, backed by FAISS when installed."""

    def __init__(self, centroids: np.ndarray):
        self.centroids = centroids
        self.backend = "numpy"
        self._faiss = None
        try:
            import faiss

            index = faiss.IndexFlatL2(centroids.shape[1])
            index.add(centroids)
            self._faiss = index
            self.backend = "faiss"
        except Exception:
            pass

    def search(self, vecs: np.ndarray):
        if self._faiss is not None:
            dist, idx = self._faiss.search(vecs, 1)
            return np.sqrt(dist[:, 0]), idx[:, 0]
        # numpy fallback: squared L2 to every centroid.
        d2 = ((vecs[:, None, :] - self.centroids[None, :, :]) ** 2).sum(axis=2)
        idx = d2.argmin(axis=1)
        return np.sqrt(d2[np.arange(len(vecs)), idx]), idx


def run() -> dict:
    config.ensure_dirs()
    if not config.WRANGLED_PARQUET.exists():
        sys.exit(f"{config.WRANGLED_PARQUET} not found. Run stage 2 first.")

    cur = duckdb.connect().execute(
        f"SELECT * FROM read_parquet('{config.WRANGLED_PARQUET.as_posix()}')"
    )
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    embedder = get_embedder()
    print(f"[embed] backend={embedder.name} rows={len(rows)}")

    categories, centroids = _build_centroids(embedder)
    index = _CentroidIndex(centroids)
    print(f"[embed] centroid index backend={index.backend}")

    vecs = embedder.encode([r["txn_purpose"] for r in rows])
    distances, assigned = index.search(vecs)

    mu, sigma = float(distances.mean()), float(distances.std())
    threshold = mu + config.ANOMALY_SIGMA * sigma

    n_flagged = 0
    with config.CLASSIFIED_JSONL.open("w") as out:
        for i, r in enumerate(rows):
            is_anom = bool(distances[i] > threshold)
            n_flagged += int(is_anom)
            rec = {
                "id": r["id"],
                "ref_area": r["ref_area"],
                "institution_id": r["institution_id"],
                "asset_class": r["asset_class"],
                "time_period": r["time_period"],
                "obs_value": float(r["obs_value"]),
                "currency": r["currency"],
                "txn_purpose": r["txn_purpose"],
                "predicted_category": categories[int(assigned[i])],
                "anomaly_score": round(float(distances[i]), 4),
                "is_anomaly": is_anom,
            }
            out.write(json.dumps(rec) + "\n")

    print(
        f"[embed] threshold={threshold:.4f} (mu={mu:.4f}, sigma={sigma:.4f}) "
        f"flagged={n_flagged} -> {config.CLASSIFIED_JSONL}"
    )
    return {"rows": len(rows), "flagged": n_flagged, "threshold": threshold}


if __name__ == "__main__":
    run()
