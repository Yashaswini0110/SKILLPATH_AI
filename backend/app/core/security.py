from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import settings
from app.core.enums import TokenType


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes")
    hashed = bcrypt.hashpw(
        password_bytes, bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    )
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _now() -> datetime:
    return datetime.now(UTC)


def create_token(
    subject: str,
    role: str,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: str | None = None,
) -> tuple[str, str, datetime]:
    token_jti = jti or str(uuid4())
    expire = _now() + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type.value,
        "jti": token_jti,
        "exp": expire,
        "iat": _now(),
    }
    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded, token_jti, expire


def create_access_token(subject: str, role: str) -> tuple[str, str, datetime]:
    return create_token(
        subject=subject,
        role=role,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str, role: str) -> tuple[str, str, datetime]:
    return create_token(
        subject=subject,
        role=role,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
