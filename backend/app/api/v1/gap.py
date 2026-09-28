from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.gap import GapAnalysisPublic
from app.services.gap_service import gap_service

router = APIRouter(prefix="/gap-analysis", tags=["gap-analysis"])


@router.get("", response_model=APIResponse[GapAnalysisPublic])
def get_gap_analysis(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[GapAnalysisPublic]:
    return APIResponse(
        data=gap_service.analyze(
            db,
            user,
            role_id=role_id,
            job_description_id=job_description_id,
        )
    )
