from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession, ListParams
from app.schemas.assessment import (
    AssessmentAttemptPublic,
    AssessmentAttemptSubmit,
    AssessmentDetailPublic,
    AssessmentSummaryPublic,
)
from app.schemas.common import APIResponse
from app.schemas.pagination import PagePublic
from app.services.assessment_service import assessment_service
from app.services.pagination import paginate

router = APIRouter(prefix="/assessments", tags=["assessments"])

ASSESSMENT_SORT = {
    "title": lambda item: item.title.lower(),
    "skill": lambda item: item.skill.name.lower(),
}


@router.get("", response_model=APIResponse[PagePublic[AssessmentSummaryPublic]])
def list_assessments(
    user: CurrentUser,
    db: DBSession,
    listing: ListParams,
    skill_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[PagePublic[AssessmentSummaryPublic]]:
    return APIResponse(
        data=paginate(
            assessment_service.list_for_user(db, user, skill_id=skill_id),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=ASSESSMENT_SORT,
        )
    )


@router.get("/{assessment_id}", response_model=APIResponse[AssessmentDetailPublic])
def get_assessment(
    assessment_id: UUID, db: DBSession, _user: CurrentUser
) -> APIResponse[AssessmentDetailPublic]:
    return APIResponse(data=assessment_service.get_detail(db, assessment_id))


@router.post(
    "/{assessment_id}/attempts",
    response_model=APIResponse[AssessmentAttemptPublic],
)
def submit_assessment(
    assessment_id: UUID,
    payload: AssessmentAttemptSubmit,
    user: CurrentUser,
    db: DBSession,
) -> APIResponse[AssessmentAttemptPublic]:
    return APIResponse(
        data=assessment_service.submit(db, user, assessment_id, payload.answers)
    )
