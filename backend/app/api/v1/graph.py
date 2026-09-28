from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.graph import (
    GraphGapMentorPublic,
    GraphSkillViewPublic,
    GraphStatusPublic,
)
from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/status", response_model=APIResponse[GraphStatusPublic])
def graph_status(_user: CurrentUser) -> APIResponse[GraphStatusPublic]:
    return APIResponse(data=graph_service.status())


@router.get("/skills/{skill_id}", response_model=APIResponse[GraphSkillViewPublic])
def graph_skill(
    skill_id: UUID, _user: CurrentUser, db: DBSession
) -> APIResponse[GraphSkillViewPublic]:
    return APIResponse(data=graph_service.skill_view(db, skill_id))


@router.get("/gap-mentors", response_model=APIResponse[list[GraphGapMentorPublic]])
def graph_gap_mentors(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[list[GraphGapMentorPublic]]:
    return APIResponse(
        data=graph_service.gap_mentors(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
    )
