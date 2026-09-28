"""Retrieve grounded passages for the learning assistant.

Employee context and catalog text are scored against the question.
Nothing is generated here. Missing context stays missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from recommendation.baselines.semantic import (
    HashingEncoder,
    MiniLMEncoder,
    get_encoder,
    semantic_score,
    tokenize,
)

ALWAYS_TYPES = frozenset({"PROFILE", "GAP", "PATH", "PATH_OVERVIEW", "ASSESSMENT"})


@dataclass
class Chunk:
    source_type: str
    title: str
    text: str
    source_id: str | None = None
    score: float = 0.0
    facts: dict[str, str] = field(default_factory=dict)


def default_encoder(
    backend: str = "hashing", model_name: str = "all-MiniLM-L6-v2"
) -> HashingEncoder | MiniLMEncoder:
    return get_encoder(backend, model_name)


def chunk_score(
    question: str,
    chunk: Chunk,
    encoder: HashingEncoder | MiniLMEncoder,
) -> float:
    haystack = f"{chunk.title}. {chunk.text}"
    cosine = semantic_score(question, haystack, encoder)
    question_tokens = set(tokenize(question))
    chunk_tokens = set(tokenize(haystack))
    if not question_tokens:
        overlap = 0.0
    else:
        overlap = len(question_tokens & chunk_tokens) / len(question_tokens)
    return round(0.35 * cosine + 0.65 * overlap, 4)


def retrieve(
    question: str,
    chunks: list[Chunk],
    *,
    encoder: HashingEncoder | MiniLMEncoder | None = None,
    limit: int = 8,
    min_score: float = 0.12,
    keep_learner: bool = True,
) -> list[Chunk]:
    encoder = encoder or HashingEncoder()
    scored: list[Chunk] = []
    for chunk in chunks:
        score = chunk_score(question, chunk, encoder)
        if keep_learner and chunk.source_type in ALWAYS_TYPES:
            score = max(score, 0.2)
        scored.append(replace(chunk, score=score))
    scored.sort(key=lambda item: (-item.score, item.title.lower()))
    picked: list[Chunk] = []
    seen: set[tuple[str, str]] = set()
    for chunk in scored:
        if chunk.score < min_score and chunk.source_type not in ALWAYS_TYPES:
            continue
        key = (chunk.source_type, chunk.title)
        if key in seen:
            continue
        seen.add(key)
        picked.append(chunk)
        if len(picked) >= limit:
            break
    return picked
