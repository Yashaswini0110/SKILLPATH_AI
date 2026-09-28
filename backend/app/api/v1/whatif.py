from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.whatif import WhatIfSimulationPublic
from app.services.whatif_service import whatif_service

router = APIRouter(prefix="/what-if", tags=["what-if"])


@router.get("", response_model=APIResponse[WhatIfSimulationPublic])
def compare_roles(
    user: CurrentUser,
    db: DBSession,
    role_ids: Annotated[list[UUID], Query(min_length=1, max_length=4)],
) -> APIResponse[WhatIfSimulationPublic]:
    return APIResponse(data=whatif_service.compare(db, user, role_ids))
