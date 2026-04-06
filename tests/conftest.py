"""
Pytest fixtures shared across all test modules.

The test strategy uses FastAPI's dependency_overrides to inject a MagicMock
in place of the real SQLAlchemy Session.  This avoids the need for a live
PostgreSQL instance while still exercising route logic and service code.
"""
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.services.auth_service import get_current_user


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_user(role: str = "borrower") -> SimpleNamespace:
    """Return a plain namespace that mimics a User ORM row."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=f"test_{role}@example.com",
        name=f"Test {role.capitalize()}",
        role=role,
        kyc_verified=False,
    )


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_db() -> MagicMock:
    """A MagicMock that stands in for a SQLAlchemy Session."""
    db = MagicMock()
    # Default: any .query().filter().first() call returns None (nothing found)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture()
def borrower() -> SimpleNamespace:
    return _make_user("borrower")


@pytest.fixture()
def lender() -> SimpleNamespace:
    return _make_user("lender")


@pytest.fixture()
def client(mock_db: MagicMock) -> TestClient:
    """Unauthenticated test client with a mocked DB session."""
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def borrower_client(mock_db: MagicMock, borrower: SimpleNamespace) -> TestClient:
    """Test client authenticated as a borrower."""
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: borrower
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def lender_client(mock_db: MagicMock, lender: SimpleNamespace) -> TestClient:
    """Test client authenticated as a lender."""
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: lender
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
