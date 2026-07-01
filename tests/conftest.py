"""
conftest.py — PyTest fixtures for isolated test database.

Uses an in-memory SQLite database so tests NEVER touch dev/prod data.
Each test function gets a fresh DB session via the `db_session` fixture,
and the full test client via the `client` fixture.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite — isolated per test run, no Postgres required for tests
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite://"  # pure in-memory, no file

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # same connection shared across threads in tests
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function", autouse=False)
def db_session():
    """Yield a clean DB session backed by in-memory SQLite."""
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with the real DB dependency overridden to use
    the in-memory test session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reusable payload factories
# ---------------------------------------------------------------------------

def low_risk_payload():
    return {
        "applicant_name": "Alice Smith",
        "annual_income": 120000.0,
        "existing_debt": 10000.0,
        "credit_score": 780,
        "loan_amount_requested": 20000.0,
        "employment_status": "employed",
    }


def high_risk_payload():
    return {
        "applicant_name": "Bob Jones",
        "annual_income": 30000.0,
        "existing_debt": 25000.0,
        "credit_score": 520,
        "loan_amount_requested": 50000.0,
        "employment_status": "unemployed",
    }


def medium_risk_payload():
    return {
        "applicant_name": "Carol Lee",
        "annual_income": 60000.0,
        "existing_debt": 20000.0,
        "credit_score": 640,
        "loan_amount_requested": 15000.0,
        "employment_status": "self_employed",
    }
