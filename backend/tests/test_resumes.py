
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pydantic import SecretStr

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User


@pytest.fixture
def test_db():
    """Create an isolated in-memory database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(test_db, monkeypatch):
    """Provide a test client authenticated as a test user."""
    # Use a test-only JWT secret; never depend on a production secret.
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        SecretStr("test-only-secret-key-for-resumez"),
    )

    with test_db() as db:
        user = User(
            email="test@example.com",
            hashed_password=hash_password("TestPassword123!"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    token = create_access_token(str(user_id))

    with TestClient(app) as test_client:
        test_client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )
        yield test_client


def create_resume(client, title="Test Resume"):
    """Create a resume and return its response."""
    return client.post(
        "/api/v1/resumes",
        json={
            "title": title,
            "target_job": "AI/ML Engineer Intern",
            "resume_data": {
                "full_name": "Test User",
                "skills": ["Python", "Machine Learning"],
            },
        },
    )


def test_create_resume(client):
    response = create_resume(client)

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "Test Resume"
    assert data["target_job"] == "AI/ML Engineer Intern"
    assert data["resume_data"]["skills"] == [
        "Python",
        "Machine Learning",
    ]


def test_list_resumes(client):
    created = create_resume(client, "Saved Resume")
    assert created.status_code == 201, created.text

    response = client.get("/api/v1/resumes")

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Saved Resume"


def test_update_resume(client):
    created = create_resume(client, "Original Resume")
    assert created.status_code == 201, created.text
    resume_id = created.json()["id"]

    response = client.put(
        f"/api/v1/resumes/{resume_id}",
        json={
            "title": "Updated Resume",
            "target_job": "AI/ML Engineer",
            "resume_data": {
                "skills": ["Python", "Machine Learning"]
            },
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Updated Resume"
    assert data["target_job"] == "AI/ML Engineer"
    assert data["resume_data"]["skills"] == [
        "Python",
        "Machine Learning",
    ]


def test_delete_resume(client):
    created = create_resume(client, "Resume to Delete")
    assert created.status_code == 201, created.text
    resume_id = created.json()["id"]

    response = client.delete(f"/api/v1/resumes/{resume_id}")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Resume deleted successfully"

    listing = client.get("/api/v1/resumes")
    assert listing.status_code == 200, listing.text
    assert all(
        resume["id"] != resume_id
        for resume in listing.json()
    )


def test_update_nonexistent_resume_returns_404(client):
    response = client.put(
        "/api/v1/resumes/999999",
        json={
            "title": "Missing Resume",
            "target_job": "AI Engineer",
            "resume_data": {},
        },
    )

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["path"] == "/api/v1/resumes/999999"


def test_delete_nonexistent_resume_returns_404(client):
    response = client.delete("/api/v1/resumes/999999")

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["path"] == "/api/v1/resumes/999999"


def test_resume_routes_require_authentication(test_db):
    # The database override is active, but this client has no JWT.
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.get("/api/v1/resumes")

    assert response.status_code == 401, response.text


def test_resume_routes_reject_invalid_token(client):
    response = client.get(
        "/api/v1/resumes",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401, response.text


def test_resume_routes_reject_inactive_user(test_db, monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        SecretStr("test-only-secret-key-for-resumez"),
    )

    with test_db() as db:
        user = User(
            email="inactive@example.com",
            hashed_password=hash_password("TestPassword123!"),
            is_active=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    token = create_access_token(str(user_id))

    with TestClient(app) as test_client:
        response = test_client.get(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401, response.text


def test_user_cannot_access_another_users_resume(client, test_db):
    # User A is already authenticated through the client fixture.
    created = create_resume(client, "User A Private Resume")
    assert created.status_code == 201, created.text
    resume_id = created.json()["id"]

    # Create a separate User B in the test database.
    with test_db() as db:
        user_b = User(
            email="userb@example.com",
            hashed_password=hash_password("TestPassword123!"),
            is_active=True,
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)
        user_b_id = user_b.id

    # Authenticate as User B.
    user_b_token = create_access_token(str(user_b_id))
    user_b_headers = {
        "Authorization": f"Bearer {user_b_token}"
    }

    # User B must not see User A's resume.
    listing = client.get(
        "/api/v1/resumes",
        headers=user_b_headers,
    )
    assert listing.status_code == 200, listing.text
    assert all(
        resume["id"] != resume_id
        for resume in listing.json()
    )

    # User B must not be able to update User A's resume.
    update = client.put(
        f"/api/v1/resumes/{resume_id}",
        headers=user_b_headers,
        json={
            "title": "Unauthorized Change",
            "target_job": "AI Engineer",
            "resume_data": {},
        },
    )
    assert update.status_code == 404, update.text

    # User B must not be able to delete User A's resume.
    delete = client.delete(
        f"/api/v1/resumes/{resume_id}",
        headers=user_b_headers,
    )
    assert delete.status_code == 404, delete.text

    # User A's resume must still exist.
    original = client.get("/api/v1/resumes")
    assert original.status_code == 200, original.text
    assert any(
        resume["id"] == resume_id
        and resume["title"] == "User A Private Resume"
        for resume in original.json()
    )
