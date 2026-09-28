"""Split resume text into coarse sections for context-aware matching."""

from __future__ import annotations

import re
from dataclasses import dataclass

SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "skills",
        re.compile(
            r"^(technical\s+)?skills?(?:\s+and\s+interests)?$|^core\s+competenc(?:y|ies)$|^technologies$",
            re.I,
        ),
    ),
    (
        "experience",
        re.compile(
            r"^(work\s+)?experience$|^employment$|^professional\s+experience$|^work\s+history$",
            re.I,
        ),
    ),
    (
        "projects",
        re.compile(r"^projects?$|^selected\s+projects$|^personal\s+projects$", re.I),
    ),
    (
        "education",
        re.compile(r"^education$|^academic\s+background$", re.I),
    ),
    (
        "summary",
        re.compile(r"^summary$|^profile$|^about(\s+me)?$|^objective$", re.I),
    ),
    (
        "certifications",
        re.compile(r"^certifications?$|^licenses$", re.I),
    ),
    (
        "required",
        re.compile(
            r"^(minimum\s+)?(requirements?|qualifications?)$|^required\s+skills?$|"
            r"^must[\s-]?haves?$|^mandatory(\s+skills?)?$",
            re.I,
        ),
    ),
    (
        "preferred",
        re.compile(
            r"^preferred(\s+qualifications?|\s+skills?)?$|^nice\s+to\s+have$|"
            r"^bonus(\s+skills?)?$|^desired(\s+skills?)?$",
            re.I,
        ),
    ),
    (
        "responsibilities",
        re.compile(
            r"^responsibilities$|^what\s+you.?ll\s+do$|^the\s+role$|^about\s+the\s+job$",
            re.I,
        ),
    ),
]


@dataclass(frozen=True)
class ResumeSection:
    name: str
    text: str
    start: int
    end: int


def segment_resume(text: str) -> list[ResumeSection]:
    if not text.strip():
        return []
    lines = text.splitlines(keepends=True)
    headings: list[tuple[int, str, int]] = []
    offset = 0
    for line in lines:
        label = _heading_label(line)
        if label:
            headings.append((offset, label, offset + len(line)))
        offset += len(line)

    if not headings:
        return [ResumeSection(name="other", text=text, start=0, end=len(text))]

    sections: list[ResumeSection] = []
    if headings[0][0] > 0:
        prefix = text[: headings[0][0]].strip()
        if prefix:
            sections.append(
                ResumeSection(name="summary", text=prefix, start=0, end=headings[0][0])
            )
    for index, (start, name, _heading_end) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append(ResumeSection(name=name, text=body, start=start, end=end))
    return sections


def section_at(sections: list[ResumeSection], char_index: int) -> str:
    for section in sections:
        if section.start <= char_index < section.end:
            return section.name
    return "other"


def _heading_label(line: str) -> str | None:
    stripped = line.strip().strip(":").strip()
    if not stripped or len(stripped) > 48:
        return None
    if stripped.endswith(".") and len(stripped.split()) > 4:
        return None
    for name, pattern in SECTION_PATTERNS:
        if pattern.match(stripped):
            return name
    return None
