
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_info_endpoint():
    response = client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json()["project"] == "ResumeZ AI"


def test_resume_validation_success():
    response = client.post(
        "/api/v1/validation-demo",
        json={
            "full_name": "Alex Sharma",
            "email": "alex@example.com",
            "target_role": "AI Engineer",
            "skills": ["Python", "FastAPI"],
        },
    )

    assert response.status_code == 200
    assert response.json()["skills_count"] == 2


def test_resume_validation_rejects_empty_skills():
    response = client.post(
        "/api/v1/validation-demo",
        json={
            "full_name": "Alex Sharma",
            "email": "alex@example.com",
            "target_role": "AI Engineer",
            "skills": [],
        },
    )

    assert response.status_code == 422


def test_unknown_route_returns_custom_404():
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
