from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.twin import TwinSnapshotPublic
from app.services.twin_service import twin_service

router = APIRouter(prefix="/twin", tags=["twin"])


@router.get("", response_model=APIResponse[TwinSnapshotPublic])
def get_twin(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[TwinSnapshotPublic]:
    return APIResponse(
        data=twin_service.snapshot(
            db,
            user,
            role_id=role_id,
            job_description_id=job_description_id,
        )
    )
