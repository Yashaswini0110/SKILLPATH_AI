from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagePublic(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int
    sort: str | None = None
    order: Literal["asc", "desc"] = "asc"
