from fastapi import APIRouter

from app.core.config import settings
from app.schemas.responses import (
    HomeResponse,
    HealthResponse,
    InfoResponse,
)

from app.schemas.responses import (
    HomeResponse,
    HealthResponse,
    InfoResponse,
    ResumeRequest,
)

router = APIRouter()


@router.get("/", response_model=HomeResponse)
def home():
    return {
        "message": "Welcome to ResumeZ AI",
        "status": "running",
    }


@router.get(
    f"{settings.api_v1_prefix}/health",
    response_model=HealthResponse,
)
def health_check():
    return {
        "status": "healthy",
        "service": "resumez-ai-backend",
        "environment": settings.environment,
    }


@router.get(
    f"{settings.api_v1_prefix}/info",
    response_model=InfoResponse,
)
def api_info():
    return {
        "project": "ResumeZ AI",
        "backend": "FastAPI",
        "version": settings.app_version,
        "features": [
            "Resume Builder",
            "AI Resume Improvement",
            "Resume Analysis",
            "PDF Export",
        ],
    }


@router.post("/api/v1/validation-demo")
def validate_resume_request(payload: ResumeRequest):
    return {
        "message": "Request validated successfully",
        "full_name": payload.full_name,
        "target_role": payload.target_role,
        "skills_count": len(payload.skills),
    }
