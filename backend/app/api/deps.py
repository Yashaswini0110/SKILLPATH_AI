from collections.abc import Callable
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.enums import TokenType, UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User
from app.services.auth_service import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
    except ExpiredSignatureError as exc:
        raise UnauthorizedError("Access token has expired") from exc
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid access token") from exc
    if payload.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedError("Invalid access token")
    try:
        user_id = UUID(str(payload.get("sub")))
    except (ValueError, TypeError) as exc:
        raise UnauthorizedError("Invalid access token") from exc
    return auth_service.get_user(db, user_id)


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    allowed = {role.value for role in roles}

    def _checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return _checker


class ListQuery(BaseModel):
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=50)
    sort: str | None = None
    order: Literal["asc", "desc"] = "asc"


def get_list_query(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    sort: Annotated[str | None, Query()] = None,
    order: Annotated[Literal["asc", "desc"], Query()] = "asc",
) -> ListQuery:
    return ListQuery(page=page, page_size=page_size, sort=sort, order=order)


CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[Session, Depends(get_db)]
ListParams = Annotated[ListQuery, Depends(get_list_query)]
