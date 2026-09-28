import bcrypt

from app.core.config import settings
from app.core.security import hash_password, verify_password


def test_hash_uses_configured_bcrypt_rounds() -> None:
    hashed = hash_password("Password1")
    assert hashed.startswith("$2")
    cost = int(hashed.split("$")[2])
    assert cost == settings.bcrypt_rounds
    assert cost == 12


def test_verify_password_success() -> None:
    hashed = hash_password("Password1")
    assert verify_password("Password1", hashed) is True


def test_verify_password_failure() -> None:
    hashed = hash_password("Password1")
    assert verify_password("WrongPass1", hashed) is False


def test_hashes_are_unique_due_to_salt() -> None:
    first = hash_password("Password1")
    second = hash_password("Password1")
    assert first != second
    assert bcrypt.checkpw(b"Password1", first.encode("utf-8"))
