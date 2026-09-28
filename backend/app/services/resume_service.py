from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import SkillSourceType
from app.core.exceptions import (
    NotFoundError,
    PayloadTooLargeError,
    ValidationAppError,
)
from app.core.paths import backend_root, ensure_repo_on_path
from app.models import Employee, Evidence, Resume, Skill, User
from app.schemas.resume import ExtractedSkillPublic, ResumePublic, ResumeSummary
from app.services.skill_view import to_skill_public
from app.services.taxonomy_service import mapper_from_db

ensure_repo_on_path()

from ml.skill_extraction.pipeline import extract_skills_from_text  # noqa: E402
from ml.skill_extraction.text_extraction import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    UnsupportedResumeTypeError,
    extract_text,
)


class ResumeService:
    def upload(self, db: Session, user: User, upload: UploadFile) -> ResumePublic:
        employee = self._employee(db, user)
        filename = upload.filename or "resume.txt"
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValidationAppError("Resume must be a PDF, DOCX, or TXT file")
        payload = upload.file.read()
        if len(payload) > settings.resume_max_bytes:
            raise PayloadTooLargeError(
                "Resume must be "
                f"{settings.resume_max_bytes // (1024 * 1024)}MB or smaller"
            )
        if not payload:
            raise ValidationAppError("Resume file is empty")

        resume_id = uuid.uuid4()
        stored = self._store(employee.id, resume_id, suffix, payload)
        resume = Resume(
            id=resume_id,
            employee_id=employee.id,
            original_filename=filename[:255],
            content_type=upload.content_type or "application/octet-stream",
            storage_path=str(stored),
            status="processing",
        )
        db.add(resume)
        db.flush()
        try:
            text = extract_text(stored)
            resume.extracted_text = text
            mapper = mapper_from_db(db)
            extracted = extract_skills_from_text(text, mapper)
            for item in extracted:
                mention_strength = min(
                    Decimal("1.00"),
                    Decimal("0.40") + Decimal("0.20") * item.mention_count,
                )
                db.add(
                    Evidence(
                        employee_id=employee.id,
                        skill_id=item.skill_id,
                        source_type=SkillSourceType.RESUME.value,
                        source_id=resume.id,
                        raw_text=item.evidence_snippet,
                        extracted_level=Decimal(str(item.proficiency)),
                        reliability=Decimal(str(settings.resume_reliability)),
                        recency=Decimal("1.00"),
                        strength=mention_strength.quantize(Decimal("0.01")),
                        inferred=True,
                        section=item.section,
                        match_type=item.match_type,
                        confidence=Decimal(str(item.confidence)),
                    )
                )
            resume.status = "processed"
            resume.error_message = None
        except UnsupportedResumeTypeError as exc:
            resume.status = "failed"
            resume.error_message = str(exc)
            raise ValidationAppError(str(exc)) from exc
        except Exception as exc:
            resume.status = "failed"
            resume.error_message = "Resume text could not be extracted"
            db.commit()
            raise ValidationAppError("Resume text could not be extracted") from exc
        db.commit()
        return self.get_resume(db, user, resume.id)

    def list_resumes(self, db: Session, user: User) -> list[ResumeSummary]:
        employee = self._employee(db, user)
        rows = db.scalars(
            select(Resume)
            .where(Resume.employee_id == employee.id)
            .order_by(Resume.created_at.desc())
        ).all()
        summaries: list[ResumeSummary] = []
        for row in rows:
            count = len(
                db.scalars(
                    select(Evidence.id).where(Evidence.source_id == row.id)
                ).all()
            )
            summaries.append(
                ResumeSummary(
                    id=row.id,
                    original_filename=row.original_filename,
                    content_type=row.content_type,
                    status=row.status,
                    created_at=row.created_at,
                    skill_count=count,
                )
            )
        return summaries

    def get_resume(self, db: Session, user: User, resume_id: uuid.UUID) -> ResumePublic:
        employee = self._employee(db, user)
        resume = db.scalar(
            select(Resume).where(
                Resume.id == resume_id, Resume.employee_id == employee.id
            )
        )
        if resume is None:
            raise NotFoundError("Resume not found")
        evidence_rows = (
            db.scalars(
                select(Evidence)
                .options(joinedload(Evidence.skill).joinedload(Skill.aliases))
                .where(Evidence.source_id == resume.id)
            )
            .unique()
            .all()
        )
        return ResumePublic(
            id=resume.id,
            original_filename=resume.original_filename,
            content_type=resume.content_type,
            status=resume.status,
            created_at=resume.created_at,
            skill_count=len(evidence_rows),
            extracted_text=resume.extracted_text,
            error_message=resume.error_message,
            skills=[
                ExtractedSkillPublic(
                    id=row.id,
                    skill=to_skill_public(row.skill),
                    extracted_level=row.extracted_level,
                    confidence=row.confidence,
                    reliability=row.reliability,
                    strength=row.strength,
                    source_type=row.source_type,
                    inferred=row.inferred,
                    evidence_snippet=row.raw_text,
                    section=row.section,
                    match_type=row.match_type,
                )
                for row in evidence_rows
            ],
        )

    def _employee(self, db: Session, user: User) -> Employee:
        employee = db.scalar(select(Employee).where(Employee.user_id == user.id))
        if employee is None:
            raise NotFoundError("Employee profile not found")
        return employee

    def _store(
        self, employee_id: uuid.UUID, resume_id: uuid.UUID, suffix: str, payload: bytes
    ) -> Path:
        folder = backend_root() / settings.resume_upload_dir / str(employee_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{resume_id}{suffix}"
        path.write_bytes(payload)
        return path


resume_service = ResumeService()
