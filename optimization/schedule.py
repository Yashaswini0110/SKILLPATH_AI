"""Week packing for selected path steps. Does not call an LLM."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeekSpan:
    week_start: int
    week_end: int


def pack_weeks(durations: list[int], hours_per_week: int) -> list[WeekSpan]:
    weekly = max(1, int(hours_per_week))
    week = 1
    used = 0
    spans: list[WeekSpan] = []
    for duration in durations:
        remaining = max(0, int(duration))
        start = week
        if remaining == 0:
            spans.append(WeekSpan(week_start=week, week_end=week))
            continue
        while remaining > 0:
            room = weekly - used
            if room <= 0:
                week += 1
                used = 0
                room = weekly
            take = min(room, remaining)
            used += take
            remaining -= take
        spans.append(WeekSpan(week_start=start, week_end=week))
    return spans
