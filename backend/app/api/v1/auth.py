from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserPublic,
)
from app.schemas.common import APIResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[AuthResponse],
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: DBSession) -> APIResponse[AuthResponse]:
    data = auth_service.register(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )
    return APIResponse(data=data, message="Account created")


@router.post("/login", response_model=APIResponse[AuthResponse])
def login(payload: LoginRequest, db: DBSession) -> APIResponse[AuthResponse]:
    data = auth_service.login(db, email=payload.email, password=payload.password)
    return APIResponse(data=data, message="Authenticated")


@router.post("/refresh", response_model=APIResponse[AuthResponse])
def refresh(payload: RefreshRequest, db: DBSession) -> APIResponse[AuthResponse]:
    data = auth_service.refresh(db, payload.refresh_token)
    return APIResponse(data=data, message="Token refreshed")


@router.post("/logout", response_model=APIResponse[dict[str, bool]])
def logout(
    payload: LogoutRequest,
    db: DBSession,
    _user: CurrentUser,
) -> APIResponse[dict[str, bool]]:
    auth_service.logout(db, payload.refresh_token)
    return APIResponse(data={"success": True}, message="Logged out")


@router.get("/me", response_model=APIResponse[UserPublic])
def me(user: CurrentUser) -> APIResponse[UserPublic]:
    return APIResponse(data=UserPublic.model_validate(user))
