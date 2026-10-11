
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse
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


@router.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar_one()

    return {
        "database_connected": result == 1,
        "message": "Database query successful",
    }


@router.post(
    f"{settings.api_v1_prefix}/resumes",
    response_model=ResumeResponse,
    status_code=201,
)

def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
):
    resume = Resume(
        title=payload.title,
        target_job=payload.target_job,
        resume_data=payload.resume_data,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get(
    f"{settings.api_v1_prefix}/resumes",
    response_model=list[ResumeResponse],
)
def list_resumes(db: Session = Depends(get_db)):
    return db.query(Resume).order_by(Resume.id.desc()).all()
