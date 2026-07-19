"""Text embedding backends for the classification stage.

Primary backend: a local HuggingFace sentence-transformers model
(``all-MiniLM-L6-v2``) - no external API calls, matching the privacy-preserving,
bulk-classification approach favoured in central-bank SupTech work.

Fallback backend: a dependency-free deterministic hashing vectoriser (numpy
only). This keeps the pipeline fully runnable offline / in CI while preserving
the same interface, so the classification logic is identical either way.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Deterministic bag-of-hashed-tokens embedder with L2 normalisation."""

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hashing-{dim}d (offline fallback)"

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in _TOKEN_RE.findall(text.lower()):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self._vec(t) for t in texts])


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.name = f"sentence-transformers/{model_name}"

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(texts, normalize_embeddings=True),
            dtype=np.float32,
        )


def get_embedder():
    """Return the best available embedder, preferring the real local model."""
    try:
        return SentenceTransformerEmbedder()
    except Exception as exc:  # ImportError or model-download failure
        print(f"[embed] sentence-transformers unavailable ({exc}); using fallback")
        return HashingEmbedder()
