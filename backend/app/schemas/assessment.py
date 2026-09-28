from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class AssessmentSummaryPublic(ORMModel):
    id: UUID
    skill: SkillPublic
    title: str
    assessment_type: str
    question_count: int
    pass_score: float
    latest_percent: float | None = None
    latest_passed: bool | None = None
    attempt_count: int = 0


class AssessmentQuestionPublic(ORMModel):
    id: UUID
    position: int
    prompt: str
    choices: list[str]


class AssessmentDetailPublic(ORMModel):
    id: UUID
    skill: SkillPublic
    title: str
    assessment_type: str
    pass_score: float
    questions: list[AssessmentQuestionPublic] = Field(default_factory=list)


class AssessmentAnswerSubmit(ORMModel):
    question_id: UUID
    selected_index: int | None = None


class AssessmentAttemptSubmit(ORMModel):
    answers: list[AssessmentAnswerSubmit] = Field(min_length=1)


class AssessmentAnswerResultPublic(ORMModel):
    question_id: UUID
    position: int
    prompt: str
    selected_index: int | None = None
    correct_index: int
    is_correct: bool
    explanation: str | None = None


class AssessmentAttemptPublic(ORMModel):
    id: UUID
    assessment_id: UUID
    skill: SkillPublic
    percent: float
    correct_count: int
    total: int
    extracted_level: float
    passed: bool
    path_effect: str | None = None
    answers: list[AssessmentAnswerResultPublic] = Field(default_factory=list)
