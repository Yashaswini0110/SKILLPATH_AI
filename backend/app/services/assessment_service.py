from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import SkillSourceType
from app.core.evidence import source_reliability
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    Evidence,
    Skill,
    User,
)
from app.schemas.assessment import (
    AssessmentAnswerResultPublic,
    AssessmentAnswerSubmit,
    AssessmentAttemptPublic,
    AssessmentDetailPublic,
    AssessmentQuestionPublic,
    AssessmentSummaryPublic,
)
from app.services.profile_service import profile_service
from app.services.skill_view import to_skill_public

ensure_repo_on_path()

from ml.assessment.score import score_mcq  # noqa: E402
from recommendation.path.adapt import path_effect  # noqa: E402


class AssessmentService:
    def list_for_user(
        self, db: Session, user: User, skill_id: UUID | None = None
    ) -> list[AssessmentSummaryPublic]:
        employee = profile_service.get_employee_for_user(db, user)
        query = select(Assessment).options(
            joinedload(Assessment.skill).joinedload(Skill.aliases),
            joinedload(Assessment.questions),
        )
        if skill_id is not None:
            query = query.where(Assessment.skill_id == skill_id)
        rows = db.scalars(query).unique().all()
        latest = self._latest_attempts(db, employee.id)
        counts = self._attempt_counts(db, employee.id)
        summaries: list[AssessmentSummaryPublic] = []
        for row in sorted(rows, key=lambda item: item.skill.canonical_name):
            attempt = latest.get(row.skill_id)
            summaries.append(
                AssessmentSummaryPublic(
                    id=row.id,
                    skill=to_skill_public(row.skill),
                    title=row.title,
                    assessment_type=row.assessment_type,
                    question_count=len(row.questions),
                    pass_score=float(row.pass_score),
                    latest_percent=None if attempt is None else float(attempt.percent),
                    latest_passed=None if attempt is None else bool(attempt.passed),
                    attempt_count=counts.get(row.skill_id, 0),
                )
            )
        return summaries

    def get_detail(self, db: Session, assessment_id: UUID) -> AssessmentDetailPublic:
        row = self._get(db, assessment_id)
        questions = [
            AssessmentQuestionPublic(
                id=item.id,
                position=item.position,
                prompt=item.prompt,
                choices=[str(choice) for choice in item.choices],
            )
            for item in row.questions
        ]
        return AssessmentDetailPublic(
            id=row.id,
            skill=to_skill_public(row.skill),
            title=row.title,
            assessment_type=row.assessment_type,
            pass_score=float(row.pass_score),
            questions=questions,
        )

    def submit(
        self,
        db: Session,
        user: User,
        assessment_id: UUID,
        answers: list[AssessmentAnswerSubmit],
    ) -> AssessmentAttemptPublic:
        employee = profile_service.get_employee_for_user(db, user)
        row = self._get(db, assessment_id)
        if row.assessment_type != "MCQ":
            raise ValidationAppError(
                "Only MCQ assessments can be submitted in this phase"
            )
        questions = list(row.questions)
        if not questions:
            raise ValidationAppError("This assessment has no questions")
        chosen = {item.question_id: item.selected_index for item in answers}
        missing = [item.id for item in questions if item.id not in chosen]
        if missing:
            raise ValidationAppError("Submit an answer for every question")
        extra = set(chosen) - {item.id for item in questions}
        if extra:
            raise ValidationAppError("Answers include an unknown question")
        selected = [chosen[item.id] for item in questions]
        for index, question in zip(selected, questions, strict=True):
            if index is None:
                continue
            if index < 0 or index >= len(question.choices):
                raise ValidationAppError("selected_index is out of range")
        score = score_mcq(
            selected,
            [int(item.correct_index) for item in questions],
            pass_score=float(row.pass_score),
        )
        attempt = AssessmentAttempt(
            assessment_id=row.id,
            employee_id=employee.id,
            correct_count=score.correct_count,
            total=score.total,
            percent=Decimal(str(round(score.percent, 3))),
            extracted_level=Decimal(str(score.extracted_level)),
            passed=score.passed,
        )
        db.add(attempt)
        db.flush()
        public_answers: list[AssessmentAnswerResultPublic] = []
        for question, choice in zip(questions, selected, strict=True):
            is_correct = choice is not None and int(choice) == int(
                question.correct_index
            )
            db.add(
                AssessmentAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    position=question.position,
                    selected_index=choice,
                    is_correct=is_correct,
                )
            )
            public_answers.append(
                AssessmentAnswerResultPublic(
                    question_id=question.id,
                    position=question.position,
                    prompt=question.prompt,
                    selected_index=choice,
                    correct_index=int(question.correct_index),
                    is_correct=is_correct,
                    explanation=question.explanation,
                )
            )
        reliability = source_reliability(SkillSourceType.ASSESSMENT.value)
        db.add(
            Evidence(
                employee_id=employee.id,
                skill_id=row.skill_id,
                source_type=SkillSourceType.ASSESSMENT.value,
                source_id=attempt.id,
                raw_text=(
                    f"{row.title}: {score.correct_count}/{score.total} "
                    f"({round(score.percent * 100)}%)"
                ),
                extracted_level=Decimal(str(score.extracted_level)),
                reliability=Decimal(str(reliability)),
                recency=Decimal("1.00"),
                strength=Decimal(str(round(score.strength, 2))),
                inferred=False,
                section="ASSESSMENT",
                match_type="assessment",
                confidence=Decimal(str(reliability)),
            )
        )
        db.commit()
        db.refresh(attempt)
        return AssessmentAttemptPublic(
            id=attempt.id,
            assessment_id=row.id,
            skill=to_skill_public(row.skill),
            percent=float(attempt.percent),
            correct_count=attempt.correct_count,
            total=attempt.total,
            extracted_level=float(attempt.extracted_level),
            passed=attempt.passed,
            path_effect=path_effect(
                float(attempt.percent),
                weak=settings.assessment_weak_score,
                strong=settings.assessment_strong_score,
            ),
            answers=public_answers,
        )

    def ids_by_skill(self, db: Session) -> dict[UUID, UUID]:
        rows = db.execute(select(Assessment.skill_id, Assessment.id)).all()
        return {skill_id: assessment_id for skill_id, assessment_id in rows}

    def progress_by_skill(self, db: Session, employee_id: UUID) -> dict[UUID, str]:
        latest = self._latest_attempts(db, employee_id)
        statuses: dict[UUID, str] = {}
        for skill_id, attempt in latest.items():
            statuses[skill_id] = "COMPLETED" if attempt.passed else "IN_PROGRESS"
        return statuses

    def latest_percent_by_skill_name(
        self, db: Session, employee_id: UUID
    ) -> dict[str, float]:
        latest = self._latest_attempts(db, employee_id)
        percents: dict[str, float] = {}
        for attempt in latest.values():
            percents[attempt.assessment.skill.name] = float(attempt.percent)
        return percents

    def _get(self, db: Session, assessment_id: UUID) -> Assessment:
        row = db.scalar(
            select(Assessment)
            .options(
                joinedload(Assessment.skill).joinedload(Skill.aliases),
                joinedload(Assessment.questions),
            )
            .where(Assessment.id == assessment_id)
        )
        if row is None:
            raise NotFoundError("Assessment not found")
        return row

    def _latest_attempts(
        self, db: Session, employee_id: UUID
    ) -> dict[UUID, AssessmentAttempt]:
        rows = db.scalars(
            select(AssessmentAttempt)
            .options(
                joinedload(AssessmentAttempt.assessment).joinedload(Assessment.skill)
            )
            .where(AssessmentAttempt.employee_id == employee_id)
            .order_by(AssessmentAttempt.created_at.desc())
        ).all()
        latest: dict[UUID, AssessmentAttempt] = {}
        for row in rows:
            skill_id = row.assessment.skill_id
            if skill_id not in latest:
                latest[skill_id] = row
        return latest

    def _attempt_counts(self, db: Session, employee_id: UUID) -> dict[UUID, int]:
        rows = db.scalars(
            select(AssessmentAttempt)
            .options(joinedload(AssessmentAttempt.assessment))
            .where(AssessmentAttempt.employee_id == employee_id)
        ).all()
        counts: dict[UUID, int] = {}
        for row in rows:
            skill_id = row.assessment.skill_id
            counts[skill_id] = counts.get(skill_id, 0) + 1
        return counts


assessment_service = AssessmentService()
