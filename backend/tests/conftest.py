from __future__ import annotations

import os
import sys
import hashlib
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_PATH = BACKEND_ROOT / "data" / "test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["MISTRAL_API_KEY"] = ""
os.environ["CORS_ORIGINS"] = "http://127.0.0.1:8753"
os.environ["ADMIN_EMAILS"] = "tester@example.com"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import Base  # noqa: E402
from app.db.models import AuthSession, User  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator:
    engine = create_async_engine(f"sqlite+aiosqlite:///{TEST_DB_PATH}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    token = "test-auth-token"
    user = User(email="tester@example.com", password_hash="unused-in-tests")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    await db_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set("essay_auth", token)
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def guest_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def non_admin_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated user who is NOT in ADMIN_EMAILS."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        reg = await c.post(
            "/api/auth/register",
            json={"email": "regular@example.com", "password": "password123"},
        )
        assert reg.status_code == 201
        yield c
    app.dependency_overrides.clear()


# ── Postgres-backed fixtures (Wörterbuch search) ─────────────────────────────
# The dictionary lookup is built on pg_trgm; running it against the SQLite suite
# above would exercise a different implementation and prove nothing. These
# fixtures therefore need a real Postgres and skip cleanly when there isn't one
# (same spirit as the `mistral_live` marker).
PG_TEST_URL = os.environ.get(
    "TEST_POSTGRES_URL",
    "postgresql+asyncpg://wordlist:wordlist@localhost:5432/wordlist_test",
)

# These fixtures drop every table they find. Refuse to point at anything but a
# database explicitly named *_test — a typo here would wipe real data.
if not PG_TEST_URL.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
    raise RuntimeError(
        f"TEST_POSTGRES_URL must name a *_test database, got: {PG_TEST_URL}"
    )


@pytest_asyncio.fixture
async def pg_engine() -> AsyncGenerator:
    from sqlalchemy import text as _text

    engine = create_async_engine(PG_TEST_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(_text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    except Exception as exc:  # noqa: BLE001 — no Postgres here; that's allowed
        await engine.dispose()
        pytest.skip(f"Postgres unavailable at {PG_TEST_URL}: {exc}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def pg_client(pg_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client wired to Postgres."""
    async def _override_get_db():
        yield pg_session

    app.dependency_overrides[get_db] = _override_get_db
    token = "test-pg-token"
    user = User(email="pg-tester@example.com", password_hash="unused-in-tests")
    pg_session.add(user)
    await pg_session.flush()
    pg_session.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    await pg_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set("essay_auth", token)
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def pg_guest_client(pg_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Anonymous client wired to Postgres — for the public read endpoints."""
    async def _override_get_db():
        yield pg_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


from tests.helpers import essay_payload, seed_words_and_phrases
