"""Deterministic explanation facts from stored scores and evidence.

The LLM is not the recommendation engine. Facts are built only from
values already computed: matched skills, gap priority, component
scores, rank, prerequisites, difficulty, and preferences. Optional
verbalization may rephrase these facts; it cannot add new ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llm.verbalize import verbalize


@dataclass(frozen=True)
class ExplanationFact:
    key: str
    text: str
    value: str | float | int | None = None

    def as_public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"key": self.key, "text": self.text}
        if self.value is not None:
            payload["value"] = self.value
        return payload


@dataclass
class Explanation:
    facts: list[ExplanationFact] = field(default_factory=list)
    verbalization: str = ""

    def as_public(self) -> dict[str, Any]:
        return {
            "facts": [item.as_public() for item in self.facts],
            "verbalization": self.verbalization,
        }


def explain_resource(
    *,
    rank: int,
    matched: list[tuple[str, str]],
    components: dict[str, Any],
    method: str,
    formats: list[str] | None = None,
) -> Explanation:
    facts: list[ExplanationFact] = []
    names = [name for name, _ in matched if name]
    if names:
        shown = ", ".join(names[:3])
        facts.append(
            ExplanationFact(
                "gap",
                f"Addresses {shown} gap.",
                names[0],
            )
        )
        priority = matched[0][1]
        if priority:
            facts.append(
                ExplanationFact(
                    "priority",
                    f"Gap priority = {priority.title()}.",
                    priority,
                )
            )
    facts.append(ExplanationFact("rank", f"Ranking position = {rank}.", rank))
    semantic = _num(components.get("semantic"))
    if semantic is not None:
        facts.append(
            ExplanationFact(
                "semantic",
                f"Semantic similarity = {semantic:.2f}.",
                round(semantic, 2),
            )
        )
    prerequisite = _num(components.get("prerequisite"))
    if prerequisite is not None:
        if prerequisite + 1e-9 >= 1.0:
            text = "Prerequisites are satisfied."
        else:
            text = f"Prerequisites are partly met ({prerequisite:.2f})."
        facts.append(ExplanationFact("prerequisite", text, round(prerequisite, 2)))
    difficulty = _num(components.get("difficulty"))
    if difficulty is not None:
        if difficulty >= 0.75:
            text = "Difficulty matches learner level."
        else:
            text = f"Difficulty fit = {difficulty:.2f}."
        facts.append(ExplanationFact("difficulty", text, round(difficulty, 2)))
    preference = _num(components.get("preference"))
    wanted = [item for item in (formats or []) if item]
    if preference is not None and wanted and preference >= 0.99:
        facts.append(
            ExplanationFact(
                "preference",
                f"Learner prefers {', '.join(wanted)}.",
                round(preference, 2),
            )
        )
    elif preference is not None:
        facts.append(
            ExplanationFact(
                "preference",
                f"Format fit = {preference:.2f}.",
                round(preference, 2),
            )
        )
    if method == "CONTENT" and semantic is None:
        content = _num(components.get("content"))
        if content is not None:
            facts.append(
                ExplanationFact(
                    "content",
                    f"Skill-gap cosine = {content:.2f}.",
                    round(content, 2),
                )
            )
    if method == "POPULARITY":
        popularity = _num(components.get("popularity"))
        if popularity is not None:
            facts.append(
                ExplanationFact(
                    "popularity",
                    f"Catalog popularity = {popularity:.2f}.",
                    round(popularity, 2),
                )
            )
    return Explanation(facts=facts, verbalization=verbalize(facts))


def explain_practice(
    *,
    rank: int,
    skill: str,
    priority: str,
    course_title: str,
    project_title: str,
    current_level: float | None = None,
    required_level: float | None = None,
) -> Explanation:
    facts = [
        ExplanationFact("gap", f"Addresses {skill} gap.", skill),
        ExplanationFact("priority", f"Gap priority = {priority.title()}.", priority),
        ExplanationFact("rank", f"Ranking position = {rank}.", rank),
        ExplanationFact(
            "sequence",
            f"Learn {course_title}, then practice {project_title}.",
        ),
    ]
    if current_level is not None and required_level is not None:
        facts.append(
            ExplanationFact(
                "levels",
                f"Current {current_level:g}/5, required {required_level:g}/5.",
                f"{current_level}->{required_level}",
            )
        )
    return Explanation(facts=facts, verbalization=verbalize(facts))


def explain_mentor(
    *,
    rank: int,
    matched_names: list[str],
    top_count: int,
    hours: int,
    open_slots: int,
    domains: list[str] | None = None,
) -> Explanation:
    count = len(matched_names)
    skills = ", ".join(matched_names[:5])
    overlap = (
        f"{count} of your top {top_count} skill gaps match this mentor's expertise"
    )
    if skills:
        overlap += f" ({skills})"
    facts = [
        ExplanationFact("overlap", f"{overlap}.", count),
        ExplanationFact("rank", f"Ranking position = {rank}.", rank),
        ExplanationFact(
            "availability",
            f"The mentor has {hours} available hours/month.",
            hours,
        ),
        ExplanationFact(
            "workload",
            f"The mentor has {open_slots} open mentee slots.",
            open_slots,
        ),
    ]
    if domains:
        facts.append(
            ExplanationFact(
                "domains",
                f"Domains: {', '.join(domains)}.",
                ", ".join(domains),
            )
        )
    return Explanation(facts=facts, verbalization=verbalize(facts))


def explain_path_step(
    *,
    skill: str,
    kind: str,
    blocked_by: list[str],
    duration_hours: int,
    week_start: int,
    week_end: int,
    open_gap: bool,
    position: int,
    course_title: str | None = None,
    project_title: str | None = None,
    extra_hours: int | None = None,
    quiz_percent: float | None = None,
    priority: str | None = None,
) -> Explanation:
    facts: list[ExplanationFact] = []
    if open_gap:
        facts.append(ExplanationFact("gap", f"Addresses {skill} gap.", skill))
        if priority and priority != "NONE":
            facts.append(
                ExplanationFact(
                    "priority",
                    f"Gap priority = {priority.title()}.",
                    priority,
                )
            )
    elif kind == "REFRESHER":
        facts.append(
            ExplanationFact("gap", f"{skill} needs review after a weak quiz.", skill)
        )
    else:
        facts.append(
            ExplanationFact(
                "foundation",
                f"{skill} is a missing foundation on the path.",
                skill,
            )
        )
    facts.append(ExplanationFact("rank", f"Path position = {position}.", position))
    if blocked_by:
        facts.append(
            ExplanationFact(
                "prerequisite",
                f"Learn after {', '.join(blocked_by)}.",
                ", ".join(blocked_by),
            )
        )
    else:
        facts.append(ExplanationFact("prerequisite", "Prerequisites are satisfied.", 1))
    if quiz_percent is not None:
        facts.append(
            ExplanationFact(
                "assessment",
                f"Latest quiz score was {round(float(quiz_percent) * 100)}%.",
                round(float(quiz_percent), 3),
            )
        )
    if extra_hours:
        facts.append(
            ExplanationFact(
                "refresher",
                f"A review step added {int(extra_hours)} hours.",
                int(extra_hours),
            )
        )
    week = (
        f"week {week_start}"
        if week_start == week_end
        else f"weeks {week_start}–{week_end}"
    )
    facts.append(
        ExplanationFact(
            "schedule",
            f"{duration_hours} hours in {week}.",
            duration_hours,
        )
    )
    if course_title:
        facts.append(
            ExplanationFact("course", f"Course: {course_title}.", course_title)
        )
    if project_title:
        facts.append(
            ExplanationFact("project", f"Project: {project_title}.", project_title)
        )
    return Explanation(facts=facts, verbalization=verbalize(facts))


def _num(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number
