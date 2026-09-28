from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import JDSourceType
from app.core.exceptions import (
    NotFoundError,
    PayloadTooLargeError,
    ValidationAppError,
)
from app.core.paths import backend_root, ensure_repo_on_path
from app.core.requirements import configured_jd_weights
from app.models import Employee, JobDescription, JobDescriptionSkill, Skill, User
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionPublic,
    JobDescriptionSkillPublic,
    JobDescriptionSummary,
)
from app.schemas.role import RequirementWeightsPublic
from app.services.skill_view import to_skill_public
from app.services.taxonomy_service import mapper_from_db

ensure_repo_on_path()

from ml.skill_extraction.jd_extractor import extract_jd_skills  # noqa: E402
from ml.skill_extraction.text_extraction import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    UnsupportedResumeTypeError,
    extract_text,
)


class JobDescriptionService:
    def create_from_text(
        self, db: Session, user: User, payload: JobDescriptionCreate
    ) -> JobDescriptionPublic:
        employee = self._employee(db, user)
        encoded = payload.text.encode("utf-8")
        if len(encoded) > settings.jd_max_bytes:
            raise PayloadTooLargeError(
                "Job description must be "
                f"{settings.jd_max_bytes // (1024 * 1024)}MB or smaller"
            )
        return self._analyze(
            db,
            user=user,
            employee=employee,
            title=payload.title,
            text=payload.text,
            source_type=JDSourceType.PASTE,
            original_filename=None,
            content_type="text/plain",
            storage_path=None,
        )

    def create_from_file(
        self,
        db: Session,
        user: User,
        upload: UploadFile,
        title: str | None = None,
    ) -> JobDescriptionPublic:
        employee = self._employee(db, user)
        filename = upload.filename or "job-description.txt"
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValidationAppError("Job description must be a PDF, DOCX, or TXT file")
        payload = upload.file.read()
        if len(payload) > settings.jd_max_bytes:
            raise PayloadTooLargeError(
                "Job description must be "
                f"{settings.jd_max_bytes // (1024 * 1024)}MB or smaller"
            )
        if not payload:
            raise ValidationAppError("Job description file is empty")

        jd_id = uuid.uuid4()
        stored = self._store(employee.id, jd_id, suffix, payload)
        try:
            text = extract_text(stored)
        except UnsupportedResumeTypeError as exc:
            raise ValidationAppError(str(exc)) from exc
        except Exception as exc:
            raise ValidationAppError(
                "Job description text could not be extracted"
            ) from exc
        if len(text.strip()) < 20:
            raise ValidationAppError("Job description is too short")
        return self._analyze(
            db,
            user=user,
            employee=employee,
            title=title.strip() if title and title.strip() else None,
            text=text,
            source_type=JDSourceType.FILE,
            original_filename=filename[:255],
            content_type=upload.content_type or "application/octet-stream",
            storage_path=str(stored),
            jd_id=jd_id,
        )

    def list_job_descriptions(
        self, db: Session, user: User
    ) -> list[JobDescriptionSummary]:
        employee = self._employee(db, user)
        rows = (
            db.scalars(
                select(JobDescription)
                .options(joinedload(JobDescription.skills))
                .where(JobDescription.employee_id == employee.id)
                .order_by(JobDescription.created_at.desc())
            )
            .unique()
            .all()
        )
        return [
            JobDescriptionSummary(
                id=row.id,
                title=row.title,
                source_type=row.source_type,
                original_filename=row.original_filename,
                status=row.status,
                created_at=row.created_at,
                skill_count=len(row.skills),
            )
            for row in rows
        ]

    def get_job_description(
        self, db: Session, user: User, job_description_id: uuid.UUID
    ) -> JobDescriptionPublic:
        employee = self._employee(db, user)
        row = (
            db.scalars(
                select(JobDescription)
                .options(
                    joinedload(JobDescription.skills)
                    .joinedload(JobDescriptionSkill.skill)
                    .joinedload(Skill.aliases)
                )
                .where(
                    JobDescription.id == job_description_id,
                    JobDescription.employee_id == employee.id,
                )
            )
            .unique()
            .one_or_none()
        )
        if row is None:
            raise NotFoundError("Job description not found")
        return self._to_public(row)

    def _analyze(
        self,
        db: Session,
        *,
        user: User,
        employee: Employee,
        title: str | None,
        text: str,
        source_type: JDSourceType,
        original_filename: str | None,
        content_type: str,
        storage_path: str | None,
        jd_id: uuid.UUID | None = None,
    ) -> JobDescriptionPublic:
        weights = configured_jd_weights()
        job_description = JobDescription(
            id=jd_id or uuid.uuid4(),
            employee_id=employee.id,
            title=(title or _title_from_text(text))[:255],
            source_type=source_type.value,
            original_filename=original_filename,
            content_type=content_type,
            storage_path=storage_path,
            extracted_text=text,
            status="processing",
            weight_required=Decimal(str(weights.required)),
            weight_preferred=Decimal(str(weights.preferred)),
            weight_mentioned=Decimal(str(weights.mentioned)),
        )
        db.add(job_description)
        db.flush()
        try:
            mapper = mapper_from_db(db)
            extracted = extract_jd_skills(text, mapper, weights)
            for item in extracted:
                db.add(
                    JobDescriptionSkill(
                        job_description_id=job_description.id,
                        skill_id=item.skill_id,
                        requirement=item.requirement.value,
                        importance=Decimal(str(item.importance)),
                        required_level=item.required_level,
                        match_type=item.match_type,
                        mention_count=item.mention_count,
                    )
                )
            job_description.status = "processed"
            job_description.error_message = None
        except Exception as exc:
            job_description.status = "failed"
            job_description.error_message = "Job description could not be analyzed"
            db.commit()
            raise ValidationAppError("Job description could not be analyzed") from exc
        db.commit()
        return self.get_job_description(db, user, job_description.id)

    def _to_public(self, row: JobDescription) -> JobDescriptionPublic:
        skills = sorted(
            row.skills,
            key=lambda item: (
                {"REQUIRED": 0, "PREFERRED": 1, "MENTIONED": 2}.get(
                    item.requirement, 9
                ),
                -item.required_level,
                item.skill.canonical_name.lower(),
            ),
        )
        return JobDescriptionPublic(
            id=row.id,
            title=row.title,
            source_type=row.source_type,
            original_filename=row.original_filename,
            status=row.status,
            created_at=row.created_at,
            skill_count=len(skills),
            extracted_text=row.extracted_text,
            error_message=row.error_message,
            weights=RequirementWeightsPublic(
                required=row.weight_required,
                preferred=row.weight_preferred,
                mentioned=row.weight_mentioned,
            ),
            skills=[
                JobDescriptionSkillPublic(
                    id=item.id,
                    skill=to_skill_public(item.skill),
                    requirement=item.requirement,
                    importance=item.importance,
                    required_level=item.required_level,
                    match_type=item.match_type,
                    mention_count=item.mention_count,
                )
                for item in skills
            ],
        )

    def _employee(self, db: Session, user: User) -> Employee:
        employee = db.scalar(select(Employee).where(Employee.user_id == user.id))
        if employee is None:
            raise NotFoundError("Employee profile not found")
        return employee

    def _store(
        self,
        employee_id: uuid.UUID,
        job_description_id: uuid.UUID,
        suffix: str,
        payload: bytes,
    ) -> Path:
        folder = backend_root() / settings.jd_upload_dir / str(employee_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{job_description_id}{suffix}"
        path.write_bytes(payload)
        return path


def _title_from_text(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:255]
    return "Untitled job description"


job_description_service = JobDescriptionService()
