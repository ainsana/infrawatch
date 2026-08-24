from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.db.database import build_database_url, get_db_session
from backend.app.main import app

TEST_DATABASE_NAME = "infrawatch_test"


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine]:
    database_url = build_database_url().set(database=TEST_DATABASE_NAME)

    if database_url.database != TEST_DATABASE_NAME:
        raise RuntimeError("Tests must use the infrawatch_test database.")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    models.Host.metadata.create_all(engine)

    yield engine

    models.Host.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db_session() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()