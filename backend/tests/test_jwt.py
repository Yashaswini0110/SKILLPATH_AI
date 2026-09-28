from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.enums import TokenType
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
)


def test_access_token_contains_expected_claims() -> None:
    token, jti, _expires = create_access_token("user-1", "EMPLOYEE")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "EMPLOYEE"
    assert payload["type"] == TokenType.ACCESS.value
    assert payload["jti"] == jti


def test_refresh_token_type_differs_from_access() -> None:
    access, _, _ = create_access_token("user-1", "EMPLOYEE")
    refresh, _, _ = create_refresh_token("user-1", "EMPLOYEE")
    assert decode_token(access)["type"] == "access"
    assert decode_token(refresh)["type"] == "refresh"


def test_expired_token_is_rejected() -> None:
    token, _, _ = create_token(
        subject="user-1",
        role="EMPLOYEE",
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_tampered_token_is_rejected() -> None:
    token, _, _ = create_access_token("user-1", "EMPLOYEE")
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(token, "wrong-secret", algorithms=[settings.jwt_algorithm])
