"""Deterministic skill-mention normalization.

Does not expand abbreviations. Abbreviations are aliases in the taxonomy so
exact canonical matches and alias matches can carry different confidence.
"""

from __future__ import annotations

import re

_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_COMPACT = re.compile(r"[^a-z0-9]")


def normalize_skill_text(raw: str) -> str:
    text = raw.strip()
    text = _CAMEL.sub(r"\1 \2", text)
    text = text.lower().replace("&", " and ")
    text = _NON_ALNUM.sub(" ", text)
    return " ".join(text.split())


def compact_skill_text(raw: str) -> str:
    return _COMPACT.sub("", normalize_skill_text(raw))
