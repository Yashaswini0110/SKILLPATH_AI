"""Turn stored explanation facts into a paragraph.

This is not a recommendation engine. It never invents skills, scores,
or evidence. An optional LLM path may only rephrase the same facts
when configured; the default is a deterministic join.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class FactLike(Protocol):
    text: str


def verbalize(facts: Iterable[FactLike], *, use_llm: bool = False) -> str:
    sentences = [_sentence(item.text) for item in facts if item.text]
    paragraph = " ".join(sentences)
    if use_llm:
        return _llm_rephrase(paragraph, sentences)
    return paragraph


def _sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return stripped if stripped.endswith(".") else f"{stripped}."


def _llm_rephrase(paragraph: str, sentences: list[str]) -> str:
    """Reserved. Without a configured client, return the fact paragraph.

    A future LLM call must send only these sentences, never employee PII
    beyond what the facts already contain, and must not add claims.
    """
    del sentences
    return paragraph
