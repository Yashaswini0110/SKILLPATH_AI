"""Semantic baseline.

Intended encoder: sentence-transformers `all-MiniLM-L6-v2`.
Default runtime encoder is a stable hashing bag-of-words so tests and
offline laptops do not download Torch. Set REC_SEMANTIC_BACKEND=minilm
after `pip install sentence-transformers`.
"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache

from recommendation.baselines.vectors import cosine_similarity, l2_normalize

_TOKEN = re.compile(r"[a-z0-9]+")
HASH_DIM = 128


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def hashing_embed(text: str, dim: int = HASH_DIM) -> list[float]:
    values = [0.0] * dim
    for token in tokenize(text):
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % dim
        values[index] += 1.0
    return l2_normalize(values)


class HashingEncoder:
    name = "hashing"

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [hashing_embed(text) for text in texts]


class MiniLMEncoder:
    name = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in vectors]


@lru_cache(maxsize=1)
def get_encoder(backend: str, model_name: str) -> HashingEncoder | MiniLMEncoder:
    if backend == "minilm":
        try:
            return MiniLMEncoder(model_name)
        except Exception:
            return HashingEncoder()
    return HashingEncoder()


def semantic_score(
    user_text: str, resource_text: str, encoder: HashingEncoder | MiniLMEncoder
) -> float:
    left, right = encoder.encode([user_text, resource_text])
    return cosine_similarity(left, right)


def gap_summary(rows: list[tuple[str, float, str]]) -> str:
    if not rows:
        return "No open skill gaps."
    parts = [
        f"{name} gap {gap:.2f} priority {priority}" for name, gap, priority in rows
    ]
    return "Employee skill gaps: " + "; ".join(parts)


def resource_text(title: str, description: str, skills: list[str]) -> str:
    skill_line = ", ".join(skills)
    return f"{title}. {description} Skills: {skill_line}."
