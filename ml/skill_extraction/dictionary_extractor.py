"""Layer 1 dictionary matcher: longest catalog phrase wins; unknown terms are ignored."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from ml.skill_extraction.segmenter import ResumeSection, section_at
from ml.skill_extraction.taxonomy_mapper import MatchType, TaxonomyMapper

AMBIGUOUS_TERMS = {"react", "rest", "git", "go", "java"}
TECH_CONTEXT = (
    "developed",
    "built",
    "using",
    "used",
    "python",
    "javascript",
    "frontend",
    "backend",
    "component",
    "api",
    "framework",
    "library",
    "docker",
    "kubernetes",
    "sql",
    "machine learning",
)


@dataclass(frozen=True)
class DictionaryHit:
    skill_id: UUID
    canonical_name: str
    matched_term: str
    match_type: MatchType
    start: int
    end: int
    snippet: str
    section: str


def extract_dictionary_hits(
    text: str,
    mapper: TaxonomyMapper,
    sections: list[ResumeSection],
) -> list[DictionaryHit]:
    occupied: list[tuple[int, int]] = []
    hits: list[DictionaryHit] = []
    surfaces = sorted(
        mapper.surface_forms(),
        key=lambda item: (len(item[0]), item[0].lower()),
        reverse=True,
    )
    seen_spans: set[tuple[int, int, str]] = set()
    for term, skill_id, canonical_name, match_type in surfaces:
        pattern = _term_pattern(term)
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            key = (start, end, str(skill_id))
            if key in seen_spans or _overlaps(start, end, occupied):
                continue
            section = section_at(sections, start)
            if not _accept_match(term, section, text, start, end):
                continue
            snippet = _snippet(text, start, end)
            hits.append(
                DictionaryHit(
                    skill_id=skill_id,
                    canonical_name=canonical_name,
                    matched_term=match.group(0),
                    match_type=match_type,
                    start=start,
                    end=end,
                    snippet=snippet,
                    section=section,
                )
            )
            occupied.append((start, end))
            seen_spans.add(key)
    hits.sort(key=lambda hit: hit.start)
    return hits


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.search(r"[A-Za-z0-9]$", term) and re.search(r"^[A-Za-z0-9]", term):
        return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.I)
    return re.compile(escaped, re.I)


def _overlaps(start: int, end: int, occupied: list[tuple[int, int]]) -> bool:
    return any(
        start < other_end and end > other_start for other_start, other_end in occupied
    )


def _accept_match(term: str, section: str, text: str, start: int, end: int) -> bool:
    normalized = term.strip().lower()
    if section in {
        "skills",
        "projects",
        "certifications",
        "required",
        "preferred",
        "responsibilities",
    }:
        return True
    if normalized in AMBIGUOUS_TERMS:
        window = text[max(0, start - 80) : min(len(text), end + 80)].lower()
        return any(token in window for token in TECH_CONTEXT)
    if len(normalized) <= 2 and section not in {"skills", "projects"}:
        original = text[start:end]
        return any(char.isupper() or char.isdigit() for char in original)
    return True


def _snippet(text: str, start: int, end: int, radius: int = 110) -> str:
    line_start = text.rfind("\n", 0, start)
    line_start = 0 if line_start == -1 else line_start + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end
    line = text[line_start:line_end].strip()
    if 8 <= len(line) <= 160:
        return " ".join(line.split())

    left = max(0, start - radius)
    right = min(len(text), end + radius)
    while left > 0 and (text[left].isalnum() or text[left] in "'-"):
        left -= 1
    while right < len(text) and (text[right].isalnum() or text[right] in "'-"):
        right += 1
    while left < start and text[left] in " \t,;:/|":
        left += 1
    chunk = " ".join(text[left:right].replace("\n", " ").split())
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(text) else ""
    return f"{prefix}{chunk}{suffix}"
