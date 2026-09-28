from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AssistantSourcePublic(BaseModel):
    source_type: str
    title: str
    text: str
    source_id: str | None = None


class AssistantAnswerPublic(ORMModel):
    id: UUID
    question: str
    answer: str
    sources: list[AssistantSourcePublic] = Field(default_factory=list)
    used_llm: bool = False
    unavailable: bool = False
