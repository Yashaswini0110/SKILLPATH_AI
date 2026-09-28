from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, require_roles
from app.core.enums import UserRole
from app.models import User
from app.schemas.analytics import AnalyticsSnapshotPublic
from app.schemas.common import APIResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

AnalyticsUser = Annotated[
    User,
    Depends(require_roles(UserRole.MANAGER, UserRole.HR_ADMIN, UserRole.SYSTEM_ADMIN)),
]


@router.get("", response_model=APIResponse[AnalyticsSnapshotPublic])
def get_analytics(
    user: AnalyticsUser,
    db: DBSession,
    department: Annotated[str | None, Query()] = None,
) -> APIResponse[AnalyticsSnapshotPublic]:
    return APIResponse(data=analytics_service.snapshot(db, user, department=department))
