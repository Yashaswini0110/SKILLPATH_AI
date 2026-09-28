"""In-memory page/sort helper for catalog-sized lists."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any, Literal

from app.core.exceptions import ValidationAppError
from app.schemas.pagination import PagePublic

SortKey = Callable[[Any], Any]


def paginate(
    rows: Sequence[Any],
    *,
    page: int,
    page_size: int,
    sort: str | None,
    order: Literal["asc", "desc"],
    allowed: dict[str, SortKey],
) -> PagePublic[Any]:
    if sort is not None and sort not in allowed:
        names = ", ".join(sorted(allowed))
        raise ValidationAppError(f"sort must be one of: {names}")
    items = list(rows)
    if sort is not None:
        items.sort(key=allowed[sort], reverse=order == "desc")
    total = len(items)
    start = (page - 1) * page_size
    sliced = items[start : start + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    return PagePublic(
        items=sliced,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        sort=sort,
        order=order,
    )
