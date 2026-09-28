"""Assessment-driven skip / refresher before the hour-budget optimizer.

A weak quiz adds review hours on that skill so dependents pack later.
A strong quiz drops the skill from the candidate list so later skills can
fit. The hour-budget optimizer then runs on the adapted order.

The LLM is not used. Course/project completion, GitHub, and mentor
feedback are not triggers here; those sources have no completion data
yet. A manual skill update already retriggers because GET /learning-paths
rebuilds from the current profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

WEAK_SCORE = 0.55
STRONG_SCORE = 0.90
REFRESHER_MIN_HOURS = 4


@dataclass(frozen=True)
class Adaptation:
    skill: str
    action: str
    percent: float
    extra_hours: int = 0
    reason: str = ""

    def as_public(self) -> dict[str, object]:
        return {
            "skill": self.skill,
            "action": self.action,
            "percent": round(float(self.percent), 3),
            "extra_hours": int(self.extra_hours),
            "reason": self.reason,
        }


@dataclass
class AdaptedPath:
    ordered: list[str]
    gap_names: set[str]
    skipped: list[str]
    extras: dict[str, int]
    adaptations: list[Adaptation] = field(default_factory=list)


def path_effect(
    percent: float,
    *,
    weak: float = WEAK_SCORE,
    strong: float = STRONG_SCORE,
) -> str | None:
    score = float(percent)
    if score + 1e-9 >= float(strong):
        return "SKIP"
    if score < float(weak):
        return "REFRESHER"
    return None


def refresher_hours(duration: int) -> int:
    return max(REFRESHER_MIN_HOURS, int(duration) // 2)


def adapt_path(
    ordered: list[str],
    percents: dict[str, float],
    *,
    gap_names: set[str],
    durations: dict[str, int] | None = None,
    weak: float = WEAK_SCORE,
    strong: float = STRONG_SCORE,
) -> AdaptedPath:
    hours = durations or {}
    kept: list[str] = []
    skipped: list[str] = []
    extras: dict[str, int] = {}
    adaptations: list[Adaptation] = []
    handled: set[str] = set()

    for name in ordered:
        percent = percents.get(name)
        if percent is None:
            kept.append(name)
            continue
        effect = path_effect(percent, weak=weak, strong=strong)
        if effect == "SKIP":
            skipped.append(name)
            adaptations.append(
                Adaptation(
                    skill=name,
                    action="SKIP",
                    percent=percent,
                    reason=_skip_reason(name, percent),
                )
            )
            handled.add(name)
            continue
        if effect == "REFRESHER":
            extra = refresher_hours(hours.get(name, 0))
            extras[name] = extra
            adaptations.append(
                Adaptation(
                    skill=name,
                    action="REFRESHER",
                    percent=percent,
                    extra_hours=extra,
                    reason=_refresher_reason(name, percent, extra),
                )
            )
            handled.add(name)
        kept.append(name)

    for name, percent in percents.items():
        if name in handled:
            continue
        if path_effect(percent, weak=weak, strong=strong) != "SKIP":
            continue
        skipped.append(name)
        adaptations.append(
            Adaptation(
                skill=name,
                action="SKIP",
                percent=percent,
                reason=_skip_reason(name, percent),
            )
        )

    return AdaptedPath(
        ordered=kept,
        gap_names=set(gap_names) - set(skipped),
        skipped=skipped,
        extras=extras,
        adaptations=adaptations,
    )


def _skip_reason(name: str, percent: float) -> str:
    return (
        f"{name} quiz was {round(percent * 100)}%, so basics were skipped "
        "and later skills can start sooner."
    )


def _refresher_reason(name: str, percent: float, extra: int) -> str:
    return (
        f"{name} quiz was {round(percent * 100)}%, so a review step added "
        f"{extra} hours and later skills may start later."
    )
