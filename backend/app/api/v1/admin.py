from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.models import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role not in {UserRole.SYSTEM_ADMIN.value, UserRole.HR_ADMIN.value}:
        raise ForbiddenError("Administrator role required")
    return user


@router.get("/ping", response_model=APIResponse[dict[str, str]])
def admin_ping(
    user: Annotated[User, Depends(_require_admin)],
) -> APIResponse[dict[str, str]]:
    return APIResponse(data={"status": "ok", "role": user.role})
