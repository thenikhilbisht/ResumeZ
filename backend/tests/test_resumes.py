
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    # Use a temporary in-memory SQLite database for tests.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_create_resume(client):
    response = client.post(
        "/api/v1/resumes",
        json={
            "title": "Test Resume",
            "target_job": "AI/ML Engineer Intern",
            "resume_data": {
                "full_name": "Test User",
                "skills": ["Python", "Machine Learning"],
            },
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "Test Resume"
    assert data["target_job"] == "AI/ML Engineer Intern"
    assert data["resume_data"]["skills"] == [
        "Python",
        "Machine Learning",
    ]


def test_list_resumes(client):
    client.post(
        "/api/v1/resumes",
        json={
            "title": "Saved Resume",
            "target_job": "Python Developer",
            "resume_data": {"skills": ["Python"]},
        },
    )

    response = client.get("/api/v1/resumes")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Saved Resume"
    assert data[0]["target_job"] == "Python Developer"
