import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Apply cross-dialect patch for in-memory SQLite spatial tests
from geoalchemy2.admin.dialects import sqlite
sqlite.after_create = lambda *args, **kwargs: None
sqlite.before_create = lambda *args, **kwargs: None
sqlite.after_drop = lambda *args, **kwargs: None
sqlite.before_drop = lambda *args, **kwargs: None

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models  # Ensure models are loaded and registered with Base.metadata


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

