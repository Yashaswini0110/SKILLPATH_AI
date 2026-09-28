from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import SkillSourceType
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models import (
    Education,
    Employee,
    EmployeeSkill,
    Evidence,
    Skill,
    TargetRole,
    User,
    WorkExperience,
)
from app.schemas.employee import (
    CompletenessBreakdown,
    CompletenessScore,
    EmployeePublic,
    EmployeeSkillCreate,
    EmployeeSkillPublic,
    EmployeeSkillUpdate,
    EmployeeUpdate,
)
from app.schemas.profile import (
    EducationCreate,
    EducationPublic,
    EducationUpdate,
    ExperienceCreate,
    ExperiencePublic,
    ExperienceUpdate,
)
from app.schemas.role import TargetRoleSummary
from app.services.skill_view import to_skill_public

COMPLETENESS_ITEMS = 8


class ProfileService:
    def get_employee_for_user(self, db: Session, user: User) -> Employee:
        employee = (
            db.scalars(
                select(Employee)
                .options(
                    joinedload(Employee.user),
                    joinedload(Employee.target_role),
                    joinedload(Employee.education),
                    joinedload(Employee.experience),
                    joinedload(Employee.skills)
                    .joinedload(EmployeeSkill.skill)
                    .joinedload(Skill.aliases),
                )
                .where(Employee.user_id == user.id)
            )
            .unique()
            .one_or_none()
        )
        if employee is None:
            raise NotFoundError("Employee profile not found")
        return employee

    def get_profile(self, db: Session, user: User) -> EmployeePublic:
        employee = self.get_employee_for_user(db, user)
        return self.to_public(employee)

    def update_profile(
        self, db: Session, user: User, payload: EmployeeUpdate
    ) -> EmployeePublic:
        employee = self.get_employee_for_user(db, user)
        data = payload.model_dump(exclude_unset=True)
        if "target_role_id" in data:
            role_id = data["target_role_id"]
            if role_id is not None:
                role = db.get(TargetRole, role_id)
                if role is None:
                    raise NotFoundError("Target role not found")
            employee.target_role_id = role_id
            del data["target_role_id"]
        if "learning_preferences" in data:
            prefs = payload.learning_preferences
            employee.learning_preferences = (
                None if prefs is None else prefs.model_dump()
            )
            del data["learning_preferences"]
        for field, value in data.items():
            setattr(employee, field, value)
        db.commit()
        return self.get_profile(db, user)

    def list_education(self, db: Session, user: User) -> list[EducationPublic]:
        employee = self.get_employee_for_user(db, user)
        return [EducationPublic.model_validate(item) for item in employee.education]

    def add_education(
        self, db: Session, user: User, payload: EducationCreate
    ) -> EducationPublic:
        employee = self.get_employee_for_user(db, user)
        item = Education(employee_id=employee.id, **payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return EducationPublic.model_validate(item)

    def update_education(
        self, db: Session, user: User, education_id: UUID, payload: EducationUpdate
    ) -> EducationPublic:
        item = self._owned_education(db, user, education_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        if item.start_year is not None and item.end_year is not None:
            if item.end_year < item.start_year:
                raise ValidationAppError("end_year cannot be before start_year")
        db.commit()
        db.refresh(item)
        return EducationPublic.model_validate(item)

    def delete_education(self, db: Session, user: User, education_id: UUID) -> None:
        item = self._owned_education(db, user, education_id)
        db.delete(item)
        db.commit()

    def list_experience(self, db: Session, user: User) -> list[ExperiencePublic]:
        employee = self.get_employee_for_user(db, user)
        return [ExperiencePublic.model_validate(item) for item in employee.experience]

    def add_experience(
        self, db: Session, user: User, payload: ExperienceCreate
    ) -> ExperiencePublic:
        employee = self.get_employee_for_user(db, user)
        item = WorkExperience(employee_id=employee.id, **payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return ExperiencePublic.model_validate(item)

    def update_experience(
        self, db: Session, user: User, experience_id: UUID, payload: ExperienceUpdate
    ) -> ExperiencePublic:
        item = self._owned_experience(db, user, experience_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(item, field, value)
        if item.is_current:
            item.end_date = None
        if item.end_date is not None and item.end_date < item.start_date:
            raise ValidationAppError("end_date cannot be before start_date")
        if not item.is_current and item.end_date is None:
            raise ValidationAppError("end_date is required unless is_current is true")
        db.commit()
        db.refresh(item)
        return ExperiencePublic.model_validate(item)

    def delete_experience(self, db: Session, user: User, experience_id: UUID) -> None:
        item = self._owned_experience(db, user, experience_id)
        db.delete(item)
        db.commit()

    def list_skills(self, db: Session, user: User) -> list[EmployeeSkillPublic]:
        employee = self.get_employee_for_user(db, user)
        return [self._skill_public(row) for row in employee.skills]

    def add_skill(
        self, db: Session, user: User, payload: EmployeeSkillCreate
    ) -> EmployeeSkillPublic:
        employee = self.get_employee_for_user(db, user)
        skill = db.get(Skill, payload.skill_id)
        if skill is None:
            raise NotFoundError("Skill not found in catalog")
        existing = db.scalar(
            select(EmployeeSkill).where(
                EmployeeSkill.employee_id == employee.id,
                EmployeeSkill.skill_id == payload.skill_id,
            )
        )
        if existing is not None:
            raise ConflictError("Skill already exists on this profile")
        row = EmployeeSkill(
            employee_id=employee.id,
            skill_id=payload.skill_id,
            current_level=payload.current_level,
            confidence=Decimal(str(settings.self_declaration_reliability)),
            source_type=SkillSourceType.SELF.value,
        )
        db.add(row)
        self._upsert_self_evidence(
            db, employee.id, payload.skill_id, payload.current_level
        )
        db.commit()
        db.refresh(row)
        db.refresh(row, attribute_names=["skill"])
        return self._skill_public(row)

    def update_skill(
        self,
        db: Session,
        user: User,
        employee_skill_id: UUID,
        payload: EmployeeSkillUpdate,
    ) -> EmployeeSkillPublic:
        row = self._owned_skill(db, user, employee_skill_id)
        row.current_level = payload.current_level
        self._upsert_self_evidence(
            db, row.employee_id, row.skill_id, payload.current_level
        )
        db.commit()
        db.refresh(row)
        return self._skill_public(row)

    def delete_skill(self, db: Session, user: User, employee_skill_id: UUID) -> None:
        row = self._owned_skill(db, user, employee_skill_id)
        self._delete_self_evidence(db, row.employee_id, row.skill_id)
        db.delete(row)
        db.commit()

    def to_public(self, employee: Employee) -> EmployeePublic:
        user = employee.user
        return EmployeePublic(
            id=employee.id,
            user_id=employee.user_id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            job_title=employee.job_title,
            department=employee.department,
            years_experience=employee.years_experience,
            available_hours_per_week=employee.available_hours_per_week,
            learning_preferences=employee.learning_preferences,
            target_role=(
                TargetRoleSummary.model_validate(employee.target_role)
                if employee.target_role is not None
                else None
            ),
            completeness=self.completeness(employee),
            education=[
                EducationPublic.model_validate(item) for item in employee.education
            ],
            experience=[
                ExperiencePublic.model_validate(item) for item in employee.experience
            ],
            skills=[self._skill_public(row) for row in employee.skills],
        )

    def completeness(self, employee: Employee) -> CompletenessScore:
        breakdown = CompletenessBreakdown(
            job_title=bool(employee.job_title),
            department=bool(employee.department),
            years_experience=employee.years_experience is not None,
            education=len(employee.education) > 0,
            experience=len(employee.experience) > 0,
            skills=len(employee.skills) > 0,
            target_role=employee.target_role_id is not None,
            learning_preferences=bool(employee.learning_preferences),
        )
        completed = sum(1 for value in breakdown.model_dump().values() if value)
        return CompletenessScore(
            score=round(completed / COMPLETENESS_ITEMS, 2),
            completed_items=completed,
            total_items=COMPLETENESS_ITEMS,
            breakdown=breakdown,
        )

    def _upsert_self_evidence(
        self,
        db: Session,
        employee_id: UUID,
        skill_id: UUID,
        level: Decimal,
    ) -> None:
        reliability = Decimal(str(settings.self_declaration_reliability))
        existing = db.scalar(
            select(Evidence).where(
                Evidence.employee_id == employee_id,
                Evidence.skill_id == skill_id,
                Evidence.source_type == SkillSourceType.SELF.value,
            )
        )
        if existing is None:
            db.add(
                Evidence(
                    employee_id=employee_id,
                    skill_id=skill_id,
                    source_type=SkillSourceType.SELF.value,
                    source_id=None,
                    raw_text=None,
                    extracted_level=level,
                    reliability=reliability,
                    recency=Decimal("1.00"),
                    strength=Decimal("1.00"),
                    inferred=False,
                    section=None,
                    match_type=None,
                    confidence=reliability,
                )
            )
            return
        existing.extracted_level = level
        existing.reliability = reliability
        existing.confidence = reliability
        existing.inferred = False

    def _delete_self_evidence(
        self, db: Session, employee_id: UUID, skill_id: UUID
    ) -> None:
        existing = db.scalar(
            select(Evidence).where(
                Evidence.employee_id == employee_id,
                Evidence.skill_id == skill_id,
                Evidence.source_type == SkillSourceType.SELF.value,
            )
        )
        if existing is not None:
            db.delete(existing)

    def _skill_public(self, row: EmployeeSkill) -> EmployeeSkillPublic:
        return EmployeeSkillPublic(
            id=row.id,
            current_level=row.current_level,
            confidence=row.confidence,
            source_type=row.source_type,
            inferred=row.source_type != SkillSourceType.SELF.value,
            skill=to_skill_public(row.skill),
        )

    def _owned_education(
        self, db: Session, user: User, education_id: UUID
    ) -> Education:
        employee = self.get_employee_for_user(db, user)
        item = db.get(Education, education_id)
        if item is None or item.employee_id != employee.id:
            raise NotFoundError("Education record not found")
        return item

    def _owned_experience(
        self, db: Session, user: User, experience_id: UUID
    ) -> WorkExperience:
        employee = self.get_employee_for_user(db, user)
        item = db.get(WorkExperience, experience_id)
        if item is None or item.employee_id != employee.id:
            raise NotFoundError("Experience record not found")
        return item

    def _owned_skill(
        self, db: Session, user: User, employee_skill_id: UUID
    ) -> EmployeeSkill:
        employee = self.get_employee_for_user(db, user)
        item = db.scalar(
            select(EmployeeSkill)
            .options(joinedload(EmployeeSkill.skill).joinedload(Skill.aliases))
            .where(EmployeeSkill.id == employee_skill_id)
        )
        if item is None or item.employee_id != employee.id:
            raise NotFoundError("Employee skill not found")
        return item


profile_service = ProfileService()
