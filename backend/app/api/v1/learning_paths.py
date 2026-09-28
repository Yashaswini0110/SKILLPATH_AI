from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.learning_path import LearningPathPublic
from app.services.path_service import path_service

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


@router.get("", response_model=APIResponse[LearningPathPublic])
def build_learning_path(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    method: Annotated[Literal["ORTOOLS", "GREEDY", "TOPOLOGICAL"], Query()] = "ORTOOLS",
    deadline_weeks: Annotated[int | None, Query(ge=1, le=52)] = None,
) -> APIResponse[LearningPathPublic]:
    return APIResponse(
        data=path_service.build(
            db,
            user,
            role_id=role_id,
            job_description_id=job_description_id,
            method=method,
            deadline_weeks=deadline_weeks,
        )
    )
