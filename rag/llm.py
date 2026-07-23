"""LLM helper for RAG answers — Ollama primary, deterministic fallback."""
from __future__ import annotations

from typing import Any


def invoke_llm(prompt: str, model: str, base_url: str) -> tuple[str | None, str]:
    """Return (text, engine). engine is 'ollama' or indicates failure reason."""
    try:
        from langchain_ollama import OllamaLLM
    except Exception:
        try:
            from langchain_community.llms import Ollama as OllamaLLM  # type: ignore
        except Exception:
            return None, "unavailable"
    try:
        llm = OllamaLLM(model=model, base_url=base_url)
        return llm.invoke(prompt).strip(), "ollama"
    except Exception:
        return None, "ollama-error"


def fallback_answer(
    question: str,
    chunks: list[dict[str, Any]],
    track: str,
) -> str:
    """Deterministic grounded answer so RAG demos run without Ollama."""
    cites = ", ".join(c["id"] for c in chunks[:3]) or "none"
    bullets = []
    for c in chunks[:3]:
        snippet = " ".join(c["text"].split())[:180]
        bullets.append(f"- [{c['id']}] {snippet}...")
    body = "\n".join(bullets) if bullets else "- No chunks retrieved."
    return (
        f"TRACK: {track}\n"
        f"QUESTION: {question}\n"
        f"ANSWER: Based on retrieved supervisory/treasury guidance, "
        f"the relevant evidence is summarised below. Citations: {cites}.\n"
        f"EVIDENCE:\n{body}\n"
        f"NOTE: Produced by the offline RAG fallback (no live LLM)."
    )


def answer_with_context(
    question: str,
    chunks: list[dict[str, Any]],
    *,
    track: str,
    model: str,
    base_url: str,
) -> dict[str, Any]:
    context = "\n\n".join(
        f"[{c['id']}] {c['title']}\n{c['text'][:1200]}" for c in chunks
    )
    prompt = f"""You are a financial supervision and treasury analytics assistant.
Answer using ONLY the retrieved context. Cite chunk IDs in square brackets.
If evidence is insufficient, say so. Do not invent market forecasts.

Track: {track}
Question: {question}

Context:
{context}

Respond with:
ANSWER: <concise grounded answer with [CHUNK-ID] citations>
RISK_HINT: <LOW|MEDIUM|HIGH|n/a>
"""
    text, engine = invoke_llm(prompt, model, base_url)
    if text is None:
        text = fallback_answer(question, chunks, track)
        engine = "rule-based"
    return {"answer": text, "engine": engine, "model": model, "track": track}
