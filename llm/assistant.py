"""Grounded answers from retrieved chunks only.

The assistant is not a recommendation engine. It turns stored profile,
gap, path, assessment, and catalog passages into plain sentences.
If a claim is not in those passages, it says the information is unavailable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from llm.retrieve import Chunk, retrieve

UNAVAILABLE = (
    "I don't have that in your profile, path, or catalog. I will not invent it."
)


@dataclass
class AssistantAnswer:
    text: str
    sources: list[Chunk]
    unavailable: bool
    used_llm: bool = False


def answer(
    question: str, chunks: list[Chunk], *, use_llm: bool = False
) -> AssistantAnswer:
    intent = classify_intent(question)
    mentioned = mentioned_titles(question, chunks)
    pool = chunks
    if intent == "GENERIC":
        pool = retrieve(question, chunks, keep_learner=True)
    selected = _select_chunks(intent, question, pool, mentioned)
    if use_llm:
        # Reserved: a future client may only rephrase selected.texts.
        pass
    if intent == "PATH":
        return _answer_path(selected)
    if intent == "NEXT":
        return _answer_next(selected)
    if intent == "WHY_NEED":
        return _answer_why_need(question, selected, mentioned)
    if intent == "PROJECT":
        return _answer_project(selected, mentioned)
    if intent == "WHY_REC":
        return _answer_why_rec(selected, mentioned)
    if intent == "EXPLAIN":
        return _answer_explain(question, selected, mentioned)
    return _answer_generic(selected)


def classify_intent(question: str) -> str:
    lowered = question.lower()
    if re.search(r"\b(project|practice)\b", lowered) and "path" not in lowered:
        return "PROJECT"
    if (
        re.search(r"why (was|is) .*(recommend|rank)", lowered)
        or "why this course" in lowered
        or re.search(r"why was this course", lowered)
    ):
        return "WHY_REC"
    if re.search(r"why (do i|should i) need", lowered) or "why do i need" in lowered:
        return "WHY_NEED"
    if _is_path_question(lowered):
        if re.search(r"\bnext\b", lowered):
            return "NEXT"
        return "PATH"
    if re.search(r"\b(next|learn next|what should i learn)\b", lowered):
        return "NEXT"
    if re.search(r"\b(explain|what is|what are)\b", lowered):
        return "EXPLAIN"
    return "GENERIC"


def _is_path_question(lowered: str) -> bool:
    if re.search(r"\b(learning path|stored path|week-by-week)\b", lowered):
        return True
    if re.search(r"\bpath\b", lowered) and re.search(
        r"\b(my|current|now|for me)\b", lowered
    ):
        return True
    return False


def mentioned_titles(question: str, chunks: list[Chunk]) -> list[str]:
    found: list[str] = []
    lowered = question.lower()
    skip = {"learner profile", "learning path", "open skill gaps"}
    candidates = sorted(
        {
            chunk.title
            for chunk in chunks
            if chunk.title and chunk.title.lower() not in skip
        },
        key=len,
        reverse=True,
    )
    for title in candidates:
        if _mentions(lowered, title) and title not in found:
            found.append(title)
    return found


def _expand_mentioned(mentioned: list[str], chunks: list[Chunk]) -> list[str]:
    extra: list[str] = []
    for chunk in chunks:
        if chunk.source_type != "SKILL":
            continue
        blob = f"{chunk.title} {chunk.text}".lower()
        if chunk.title in mentioned or any(_mentions(blob, name) for name in mentioned):
            extra.append(chunk.title)
            prefix = chunk.text.split(":", 1)[0].strip()
            if prefix:
                extra.append(prefix)
            extra.extend(
                str(chunk.facts[key])
                for key in ("name", "canonical")
                if chunk.facts.get(key)
            )
            extra.extend(
                part.strip()
                for part in chunk.facts.get("aliases", "").split(",")
                if part.strip()
            )
    merged: list[str] = []
    for name in mentioned + extra:
        if name and name not in merged:
            merged.append(name)
    return merged


def _mentions(question_lower: str, term: str) -> bool:
    stripped = term.strip()
    if not stripped or len(stripped) < 2:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(stripped.lower())}(?![a-z0-9])"
    return re.search(pattern, question_lower) is not None


def _select_chunks(
    intent: str,
    question: str,
    chunks: list[Chunk],
    mentioned: list[str],
) -> list[Chunk]:
    del question
    if intent in {"NEXT", "PATH"}:
        types = {"PROFILE", "GAP", "PATH", "PATH_OVERVIEW"}
    elif intent == "WHY_NEED":
        types = {"PROFILE", "GAP", "PATH", "SKILL"}
    elif intent == "PROJECT":
        types = {"PROJECT", "PRACTICE", "SKILL"}
    elif intent == "WHY_REC":
        types = {"RECOMMENDATION", "COURSE"}
    elif intent == "EXPLAIN":
        types = {"SKILL", "COURSE", "PROJECT"}
    else:
        types = {chunk.source_type for chunk in chunks}
    selected = [chunk for chunk in chunks if chunk.source_type in types]
    names = _expand_mentioned(mentioned, chunks)
    if names and intent not in {"PATH", "NEXT"}:
        narrowed = [
            chunk
            for chunk in selected
            if any(
                _mentions(f"{chunk.title} {chunk.text}".lower(), name) for name in names
            )
        ]
        if intent == "WHY_NEED":
            narrowed.extend(
                chunk
                for chunk in selected
                if chunk.source_type == "PROFILE" and chunk not in narrowed
            )
        if narrowed:
            selected = narrowed
    if not selected and intent in {"EXPLAIN", "PROJECT", "WHY_REC", "WHY_NEED"}:
        return []
    return selected


def _unavailable(sources: list[Chunk] | None = None) -> AssistantAnswer:
    return AssistantAnswer(
        text=UNAVAILABLE,
        sources=sources or [],
        unavailable=True,
    )


def _answer_path(chunks: list[Chunk]) -> AssistantAnswer:
    overview = next(
        (chunk for chunk in chunks if chunk.source_type == "PATH_OVERVIEW"), None
    )
    steps = [chunk for chunk in chunks if chunk.source_type == "PATH"]
    if overview is None and not steps:
        return _answer_next(chunks)
    sources = [item for item in (overview, *steps[:1]) if item is not None]
    parts: list[str] = []
    if overview is not None:
        target = overview.facts.get("target")
        start = overview.facts.get("start")
        hours = overview.facts.get("hours_per_week")
        weeks = overview.facts.get("weeks")
        sequence = overview.facts.get("sequence")
        if target:
            timing = ""
            if hours and weeks:
                timing = f" at {hours} hours/week for about {weeks} weeks"
            parts.append(f"Your stored path is for {target}{timing}.")
        if start:
            parts.append(f"Start with {start}.")
        if sequence and "→" in sequence:
            rest = [item.strip() for item in sequence.split("→")[1:4] if item.strip()]
            if len(rest) == 1:
                parts.append(f"After that comes {rest[0]}.")
            elif rest:
                parts.append("After that come " + ", ".join(rest) + ".")
        if not parts:
            parts.append(_sentence(overview.text))
    elif steps:
        first = steps[0]
        skill = first.facts.get("skill") or first.title
        parts.append(f"Your stored path starts with {skill}.")
        extra = _step_detail(first)
        if extra:
            parts.append(extra)
    if not parts:
        return AssistantAnswer(
            text=(
                "I don't have a stored learning path yet. "
                "Open Path to generate the week-by-week plan."
            ),
            sources=chunks[:1],
            unavailable=True,
        )
    return AssistantAnswer(text=" ".join(parts), sources=sources, unavailable=False)


def _answer_next(chunks: list[Chunk]) -> AssistantAnswer:
    steps = [chunk for chunk in chunks if chunk.source_type == "PATH"]
    step = steps[0] if steps else None
    if step is None:
        overview = next(
            (chunk for chunk in chunks if chunk.source_type == "PATH_OVERVIEW"),
            None,
        )
        if overview is not None and overview.facts.get("start"):
            start = overview.facts["start"]
            return AssistantAnswer(
                text=f"Start with {start}, the first step on your stored path.",
                sources=[overview],
                unavailable=False,
            )
        gap = next((chunk for chunk in chunks if chunk.source_type == "GAP"), None)
        if gap is not None:
            return AssistantAnswer(
                text=(
                    "I don't have a stored learning path yet. "
                    f"{_sentence(gap.text)} "
                    "Open Path to generate the week-by-week plan."
                ),
                sources=[gap],
                unavailable=False,
            )
        profile = next(
            (chunk for chunk in chunks if chunk.source_type == "PROFILE"), None
        )
        if profile is not None and "no target role" in profile.text.lower():
            return AssistantAnswer(
                text=(
                    "I don't have a target role or learning path yet. "
                    "Select a role on Profile first."
                ),
                sources=[profile],
                unavailable=True,
            )
        return _unavailable(chunks[:1])
    skill = step.facts.get("skill") or step.title
    detail = _step_detail(step)
    lead = f"Start with {skill}."
    return AssistantAnswer(
        text=f"{lead} {detail}".strip(),
        sources=[step],
        unavailable=False,
    )


def _step_detail(step: Chunk) -> str:
    bits: list[str] = []
    reason = step.facts.get("reason") or ""
    if reason:
        bits.append(_sentence(reason))
    course = step.facts.get("course")
    if course:
        bits.append(f"The mapped course is {course}.")
    project = step.facts.get("project")
    if project:
        bits.append(f"Then practice with {project}.")
    weeks = step.facts.get("weeks")
    hours = step.facts.get("hours")
    if weeks and hours:
        bits.append(f"It is scheduled for {weeks} ({hours}).")
    if bits:
        return " ".join(bits)
    return _sentence(step.text)


def _answer_why_need(
    _question: str, chunks: list[Chunk], mentioned: list[str]
) -> AssistantAnswer:
    if not mentioned:
        return _unavailable()
    gap = next((chunk for chunk in chunks if chunk.source_type == "GAP"), None)
    path = next((chunk for chunk in chunks if chunk.source_type == "PATH"), None)
    skill = next((chunk for chunk in chunks if chunk.source_type == "SKILL"), None)
    profile = next((chunk for chunk in chunks if chunk.source_type == "PROFILE"), None)
    name = mentioned[0]
    sources: list[Chunk] = []
    parts: list[str] = []
    if gap is not None:
        sources.append(gap)
        role = gap.facts.get("role")
        priority = gap.facts.get("priority")
        current = gap.facts.get("current")
        required = gap.facts.get("required")
        skill_name = gap.facts.get("skill") or gap.title or name
        if role and priority:
            levels = ""
            if current and required:
                levels = f" You are at {current}/5; the role asks for {required}/5."
            parts.append(
                f"You need {skill_name} for {role} because it is a "
                f"{priority.lower()} gap.{levels}"
            )
        else:
            parts.append(_sentence(gap.text))
    elif path is not None:
        sources.append(path)
        parts.append(_sentence(path.text))
    elif skill is not None:
        sources.append(skill)
        desc = _catalog_description(skill)
        role = ""
        if profile is not None:
            role = profile.facts.get("target") or ""
        if role:
            parts.append(
                f"{name} is not an open gap on your {role} path."
            )
            if desc:
                parts.append(f"The catalog describes it as {desc}.")
        elif desc:
            parts.append(f"{name} is in the catalog as {desc}.")
        else:
            parts.append(skill.text)
    if not parts:
        return AssistantAnswer(
            text=f"I don't have {name} in your skill profile, gaps, or path.",
            sources=[],
            unavailable=True,
        )
    return AssistantAnswer(text=" ".join(parts), sources=sources, unavailable=False)


def _answer_project(chunks: list[Chunk], mentioned: list[str]) -> AssistantAnswer:
    if not mentioned:
        return AssistantAnswer(
            text="Name a catalog skill to find a project. I will not invent one.",
            sources=[],
            unavailable=True,
        )
    practice = next(
        (chunk for chunk in chunks if chunk.source_type == "PRACTICE"), None
    )
    project = next((chunk for chunk in chunks if chunk.source_type == "PROJECT"), None)
    chosen = project or practice
    if chosen is None:
        label = mentioned[0]
        return AssistantAnswer(
            text=f"I don't have a catalog project for {label}.",
            sources=[],
            unavailable=True,
        )
    label = mentioned[0]
    title = chosen.facts.get("title") or chosen.title
    description = chosen.facts.get("description") or _after_label(chosen.text, title)
    description = _strip_skills_suffix(description)
    text = f"The catalog project for {label} is {title}."
    if description:
        text += f" {_sentence(description)}"
    if practice is not None and chosen is project:
        course = practice.facts.get("course")
        if course:
            text += f" Practice pairs it after {course}."
    return AssistantAnswer(
        text=text.strip(),
        sources=[chosen],
        unavailable=False,
    )


def _answer_why_rec(chunks: list[Chunk], mentioned: list[str]) -> AssistantAnswer:
    rec = next(
        (chunk for chunk in chunks if chunk.source_type == "RECOMMENDATION"), None
    )
    if rec is None:
        label = mentioned[0] if mentioned else "that course"
        return AssistantAnswer(
            text=(
                f"I don't have a stored ranking for {label}. "
                "Open Recommend first so the facts are saved."
            ),
            sources=[],
            unavailable=True,
        )
    title = rec.facts.get("title") or rec.title
    gap = rec.facts.get("gap")
    priority = rec.facts.get("priority")
    rank = rec.facts.get("rank")
    prereq = rec.facts.get("prerequisite")
    difficulty = rec.facts.get("difficulty")
    parts: list[str] = []
    if rank and rank == "1":
        parts.append(f"{title} is the top stored course on your list.")
    elif rank:
        parts.append(f"{title} is stored at rank {rank}.")
    else:
        parts.append(f"{title} is on your stored recommendation list.")
    if gap:
        why = f"It was ranked there because it addresses your {gap} gap"
        if priority:
            why += f" ({priority.lower()})"
        parts.append(why + ".")
    if prereq:
        parts.append(_sentence(prereq))
    if difficulty and "matches" in difficulty.lower():
        parts.append(_sentence(difficulty))
    return AssistantAnswer(text=" ".join(parts), sources=[rec], unavailable=False)


def _answer_explain(
    question: str, chunks: list[Chunk], mentioned: list[str]
) -> AssistantAnswer:
    if not mentioned:
        if _is_path_question(question.lower()) or "path" in question.lower():
            text = (
                "I don't have a catalog description for that topic. "
                "If you meant your learning path, ask “What is my learning path?”"
            )
        else:
            text = "I don't have a catalog description for that topic."
        return AssistantAnswer(text=text, sources=[], unavailable=True)
    if not chunks:
        label = mentioned[0]
        return AssistantAnswer(
            text=f"I don't have a catalog description for {label}.",
            sources=[],
            unavailable=True,
        )
    skill = next((chunk for chunk in chunks if chunk.source_type == "SKILL"), None)
    project = next((chunk for chunk in chunks if chunk.source_type == "PROJECT"), None)
    chosen = skill or project
    if chosen is None:
        course_only = _matching_course(chunks, mentioned)
        chosen = course_only
    if chosen is None:
        return _unavailable()
    name = mentioned[0]
    lookup = list(mentioned)
    if skill is not None:
        name = skill.facts.get("name") or skill.title
        description = _catalog_description(skill)
        lookup.extend(
            [
                skill.title,
                skill.facts.get("name", ""),
                skill.facts.get("canonical", ""),
                skill.facts.get("aliases", ""),
            ]
        )
    else:
        description = _catalog_description(chosen)
    sentence = _as_definition(name, description)
    sources = [chosen]
    course = _matching_course(chunks, lookup)
    if course is not None:
        sources.append(course)
        course_desc = course.facts.get("description") or _after_label(
            course.text, course.title
        )
        course_desc = _strip_skills_suffix(course_desc)
        sentence += f" A catalog course that teaches this is {course.title}."
        if course_desc:
            sentence += f" {_sentence(course_desc)}"
    return AssistantAnswer(text=sentence, sources=sources[:2], unavailable=False)


def _matching_course(chunks: list[Chunk], names: list[str]) -> Chunk | None:
    tokens: list[str] = []
    for name in names:
        for part in str(name).split(","):
            token = part.strip().lower()
            if len(token) >= 4 and token not in tokens:
                tokens.append(token)
    if not tokens:
        return None
    for chunk in chunks:
        if chunk.source_type != "COURSE":
            continue
        hay = chunk.title.lower()
        if any(token in hay for token in tokens):
            return chunk
    return None


def _answer_generic(chunks: list[Chunk]) -> AssistantAnswer:
    usable = [
        chunk
        for chunk in chunks
        if chunk.source_type not in {"PROFILE"} or chunk.score >= 0.25
    ]
    if not usable:
        return _unavailable()
    top = usable[0]
    if top.score < 0.18 and top.source_type not in {
        "PATH",
        "PATH_OVERVIEW",
        "GAP",
        "ASSESSMENT",
    }:
        return _unavailable([top])
    return AssistantAnswer(
        text=_sentence(top.text),
        sources=[top],
        unavailable=False,
    )


def _catalog_description(chunk: Chunk) -> str:
    raw = chunk.facts.get("description") or _after_label(chunk.text, chunk.title)
    raw = re.split(r"\sAlso called\s", raw, maxsplit=1)[0]
    return _strip_skills_suffix(raw).strip().rstrip(".")


def _as_definition(name: str, description: str) -> str:
    desc = description.strip().rstrip(".")
    if not desc:
        return f"{name} is in the catalog, but no description is stored."
    if desc.lower().startswith(name.lower() + " "):
        return _sentence(desc)
    copula = "are" if _looks_plural(name) else "is"
    if desc[0].isupper():
        desc = desc[0].lower() + desc[1:]
    return f"{name} {copula} {desc}."


def _looks_plural(name: str) -> bool:
    if name.isupper() or len(name) <= 3:
        return False
    return name.endswith("s") and not name.endswith("ss")


def _after_label(text: str, label: str) -> str:
    stripped = text.strip()
    prefix = f"{label}:"
    if stripped.lower().startswith(prefix.lower()):
        return stripped[len(prefix) :].strip()
    if ":" in stripped:
        return stripped.split(":", 1)[1].strip()
    return stripped


def _strip_skills_suffix(text: str) -> str:
    return re.split(r"\sSkills:\s", text, maxsplit=1)[0].strip()


def _sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    stripped = stripped.replace("From the catalog:", "").strip()
    return stripped if stripped.endswith(".") else f"{stripped}."
