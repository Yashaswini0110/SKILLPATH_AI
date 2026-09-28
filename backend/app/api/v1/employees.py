from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.employee import (
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
from app.schemas.skill_profile import SkillProfilePublic
from app.services.profile_service import profile_service
from app.services.skill_profile_service import skill_profile_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/me", response_model=APIResponse[EmployeePublic])
def get_me(user: CurrentUser, db: DBSession) -> APIResponse[EmployeePublic]:
    return APIResponse(data=profile_service.get_profile(db, user))


@router.put("/me", response_model=APIResponse[EmployeePublic])
def update_me(
    payload: EmployeeUpdate, user: CurrentUser, db: DBSession
) -> APIResponse[EmployeePublic]:
    return APIResponse(
        data=profile_service.update_profile(db, user, payload),
        message="Profile updated",
    )


@router.get("/me/education", response_model=APIResponse[list[EducationPublic]])
def list_education(
    user: CurrentUser, db: DBSession
) -> APIResponse[list[EducationPublic]]:
    return APIResponse(data=profile_service.list_education(db, user))


@router.post(
    "/me/education",
    response_model=APIResponse[EducationPublic],
    status_code=status.HTTP_201_CREATED,
)
def add_education(
    payload: EducationCreate, user: CurrentUser, db: DBSession
) -> APIResponse[EducationPublic]:
    return APIResponse(
        data=profile_service.add_education(db, user, payload),
        message="Education added",
    )


@router.put("/me/education/{education_id}", response_model=APIResponse[EducationPublic])
def update_education(
    education_id: UUID,
    payload: EducationUpdate,
    user: CurrentUser,
    db: DBSession,
) -> APIResponse[EducationPublic]:
    return APIResponse(
        data=profile_service.update_education(db, user, education_id, payload),
        message="Education updated",
    )


@router.delete(
    "/me/education/{education_id}", response_model=APIResponse[dict[str, bool]]
)
def delete_education(
    education_id: UUID, user: CurrentUser, db: DBSession
) -> APIResponse[dict[str, bool]]:
    profile_service.delete_education(db, user, education_id)
    return APIResponse(data={"success": True}, message="Education removed")


@router.get("/me/experience", response_model=APIResponse[list[ExperiencePublic]])
def list_experience(
    user: CurrentUser, db: DBSession
) -> APIResponse[list[ExperiencePublic]]:
    return APIResponse(data=profile_service.list_experience(db, user))


@router.post(
    "/me/experience",
    response_model=APIResponse[ExperiencePublic],
    status_code=status.HTTP_201_CREATED,
)
def add_experience(
    payload: ExperienceCreate, user: CurrentUser, db: DBSession
) -> APIResponse[ExperiencePublic]:
    return APIResponse(
        data=profile_service.add_experience(db, user, payload),
        message="Experience added",
    )


@router.put(
    "/me/experience/{experience_id}", response_model=APIResponse[ExperiencePublic]
)
def update_experience(
    experience_id: UUID,
    payload: ExperienceUpdate,
    user: CurrentUser,
    db: DBSession,
) -> APIResponse[ExperiencePublic]:
    return APIResponse(
        data=profile_service.update_experience(db, user, experience_id, payload),
        message="Experience updated",
    )


@router.delete(
    "/me/experience/{experience_id}", response_model=APIResponse[dict[str, bool]]
)
def delete_experience(
    experience_id: UUID, user: CurrentUser, db: DBSession
) -> APIResponse[dict[str, bool]]:
    profile_service.delete_experience(db, user, experience_id)
    return APIResponse(data={"success": True}, message="Experience removed")


@router.get("/me/skill-profile", response_model=APIResponse[SkillProfilePublic])
def get_skill_profile(
    user: CurrentUser, db: DBSession
) -> APIResponse[SkillProfilePublic]:
    return APIResponse(data=skill_profile_service.get_profile(db, user))


@router.get("/me/skills", response_model=APIResponse[list[EmployeeSkillPublic]])
def list_skills(
    user: CurrentUser, db: DBSession
) -> APIResponse[list[EmployeeSkillPublic]]:
    return APIResponse(data=profile_service.list_skills(db, user))


@router.post(
    "/me/skills",
    response_model=APIResponse[EmployeeSkillPublic],
    status_code=status.HTTP_201_CREATED,
)
def add_skill(
    payload: EmployeeSkillCreate, user: CurrentUser, db: DBSession
) -> APIResponse[EmployeeSkillPublic]:
    return APIResponse(
        data=profile_service.add_skill(db, user, payload),
        message="Skill added. Self-declared proficiency is not verified evidence.",
    )


@router.put(
    "/me/skills/{employee_skill_id}", response_model=APIResponse[EmployeeSkillPublic]
)
def update_skill(
    employee_skill_id: UUID,
    payload: EmployeeSkillUpdate,
    user: CurrentUser,
    db: DBSession,
) -> APIResponse[EmployeeSkillPublic]:
    return APIResponse(
        data=profile_service.update_skill(db, user, employee_skill_id, payload),
        message="Skill updated",
    )


@router.delete(
    "/me/skills/{employee_skill_id}", response_model=APIResponse[dict[str, bool]]
)
def delete_skill(
    employee_skill_id: UUID, user: CurrentUser, db: DBSession
) -> APIResponse[dict[str, bool]]:
    profile_service.delete_skill(db, user, employee_skill_id)
    return APIResponse(data={"success": True}, message="Skill removed")
