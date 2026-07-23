"""Load the synthetic markdown corpus with YAML-like front matter."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import config

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse_list(val: str) -> list[str]:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip("'\"") for x in inner.split(",")]
    return [val.strip().strip("'\"")]


def _parse_front_matter(block: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key, raw = key.strip(), raw.strip()
        if raw.startswith("["):
            meta[key] = _parse_list(raw)
        else:
            meta[key] = raw.strip("'\"")
    return meta


def load_documents(corpus_dir: Path | None = None) -> list[dict[str, Any]]:
    root = corpus_dir or config.RAG_CORPUS_DIR
    docs: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = _FM_RE.match(text)
        if m:
            meta = _parse_front_matter(m.group(1))
            body = m.group(2).strip()
        else:
            meta = {"id": path.stem, "track": "general", "topics": []}
            body = text.strip()
        docs.append(
            {
                "id": meta.get("id", path.stem),
                "path": str(path.relative_to(config.ROOT)),
                "track": meta.get("track", "general"),
                "topics": meta.get("topics") or [],
                "asset_classes": meta.get("asset_classes") or [],
                "jurisdictions": meta.get("jurisdictions") or [],
                "title": next(
                    (ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")),
                    path.stem,
                ),
                "text": body,
                "search_text": f"{meta.get('id', '')} {body}",
            }
        )
    return docs
