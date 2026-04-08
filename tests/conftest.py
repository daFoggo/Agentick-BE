from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.core.database import Database
from app.main import app


@pytest.fixture(scope="session")
def test_database_url() -> str:
    # Domain-independent default; individual suites can override via fixture shadowing.
    return "sqlite+pysqlite:///:memory:"


@pytest.fixture
def database(test_database_url: str) -> Database:
    return Database(test_database_url)


@pytest.fixture
def db_session(database: Database) -> Generator:
    with database.session() as session:
        yield session


@pytest.fixture
def client(database: Database) -> Generator[TestClient, None, None]:
    def _get_test_db() -> Generator:
        with database.session() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)