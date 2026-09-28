from datetime import UTC, datetime
from uuid import UUID

from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import TokenType, UserRole
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Employee, RefreshToken, User
from app.schemas.auth import (
    AuthResponse,
    TokenPair,
    UserPublic,
)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class AuthService:
    def register(
        self,
        db: Session,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
    ) -> AuthResponse:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role.value,
        )
        user.employee = Employee(available_hours_per_week=10)
        db.add(user)
        db.flush()
        tokens = self._issue_token_pair(db, user)
        db.commit()
        db.refresh(user)
        return AuthResponse(tokens=tokens, user=UserPublic.model_validate(user))

    def login(self, db: Session, email: str, password: str) -> AuthResponse:
        user = db.scalar(select(User).where(User.email == email))
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        tokens = self._issue_token_pair(db, user)
        db.commit()
        return AuthResponse(tokens=tokens, user=UserPublic.model_validate(user))

    def refresh(self, db: Session, refresh_token: str) -> AuthResponse:
        payload = self._decode_refresh(refresh_token)
        token_row = db.scalar(
            select(RefreshToken).where(RefreshToken.jti == payload["jti"])
        )
        if token_row is None or token_row.revoked_at is not None:
            raise UnauthorizedError("Refresh token is invalid")
        if _aware(token_row.expires_at) < datetime.now(UTC):
            raise UnauthorizedError("Refresh token has expired")

        user = db.get(User, token_row.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is inactive")

        token_row.revoked_at = datetime.now(UTC)
        tokens = self._issue_token_pair(db, user)
        db.commit()
        return AuthResponse(tokens=tokens, user=UserPublic.model_validate(user))

    def logout(self, db: Session, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = self._decode_refresh(refresh_token)
        except UnauthorizedError:
            return
        token_row = db.scalar(
            select(RefreshToken).where(RefreshToken.jti == payload["jti"])
        )
        if token_row is not None and token_row.revoked_at is None:
            token_row.revoked_at = datetime.now(UTC)
            db.commit()

    def get_user(self, db: Session, user_id: UUID) -> User:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Not authenticated")
        return user

    def _issue_token_pair(self, db: Session, user: User) -> TokenPair:
        access, _, _ = create_access_token(str(user.id), user.role)
        refresh, jti, expires_at = create_refresh_token(str(user.id), user.role)
        db.add(
            RefreshToken(
                user_id=user.id,
                jti=jti,
                expires_at=expires_at,
            )
        )
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def _decode_refresh(self, token: str) -> dict[str, str]:
        try:
            payload = decode_token(token)
        except ExpiredSignatureError as exc:
            raise UnauthorizedError("Refresh token has expired") from exc
        except InvalidTokenError as exc:
            raise UnauthorizedError("Refresh token is invalid") from exc
        if payload.get("type") != TokenType.REFRESH.value:
            raise ValidationAppError("Token is not a refresh token")
        return payload


auth_service = AuthService()
