from __future__ import annotations

import os
import uuid
from collections.abc import Generator

os.environ["SECRET_KEY"] = "test-secret-key-phase1-not-for-production-use"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["BCRYPT_ROUNDS"] = "12"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg2://skillpath:skillpath@localhost:5435/skillpath_test"
)
os.environ["REC_SEMANTIC_BACKEND"] = "hashing"
os.environ["NEO4J_SYNC_ON_STARTUP"] = "false"
os.environ["NEO4J_URI"] = "bolt://localhost:7688"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "skillpath"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, make_url, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import app.models  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_catalog  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _ensure_database(url: str) -> None:
    parsed = make_url(url)
    db_name = parsed.database
    if not db_name:
        raise RuntimeError("DATABASE_URL must include a database name")
    admin_engine = create_engine(
        parsed.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = os.environ["DATABASE_URL"]
    try:
        _ensure_database(url)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL is not available for tests: {exc}")
    test_engine = create_engine(url, future=True)
    with test_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    seed_catalog(session)
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine: Engine, db_session: Session) -> Generator[TestClient, None, None]:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def register_user(
    client: TestClient,
    email: str,
    password: str = "Password1",
    full_name: str = "Alex Johnson",
    role: str = "EMPLOYEE",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def page_items(response) -> list:
    payload = response.json()["data"]
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    return payload
