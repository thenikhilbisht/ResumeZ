from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.models import Resume, User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.schemas.responses import (
    HomeResponse,
    HealthResponse,
    InfoResponse,
    ResumeRequest,
)

router = APIRouter()


# --------------------------------------------------
# Home and system information
# --------------------------------------------------

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


# --------------------------------------------------
# Protected resume endpoints
# --------------------------------------------------

@router.post(
    f"{settings.api_v1_prefix}/resumes",
    response_model=ResumeResponse,
    status_code=201,
)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = Resume(
        user_id=current_user.id,
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
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc())
        .all()
    )


@router.put(
    f"{settings.api_v1_prefix}/resumes/{'{'}resume_id{'}'}",
    response_model=ResumeResponse,
)
def update_resume(
    resume_id: int,
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    resume.title = payload.title
    resume.target_job = payload.target_job
    resume.resume_data = payload.resume_data

    db.commit()
    db.refresh(resume)

    return resume


@router.delete(
    f"{settings.api_v1_prefix}/resumes/{'{'}resume_id{'}'}",
)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    db.delete(resume)
    db.commit()

    return {
        "message": "Resume deleted successfully",
        "resume_id": resume_id,
    }


# --------------------------------------------------
# User registration
# --------------------------------------------------

@router.post(
    f"{settings.api_v1_prefix}/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    normalized_email = str(payload.email).lower()

    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        email=normalized_email,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# --------------------------------------------------
# User login
# --------------------------------------------------

@router.post(
    f"{settings.api_v1_prefix}/auth/login",
    response_model=TokenResponse,
)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    normalized_email = str(payload.email).lower()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            payload.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(str(user.id))

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# --------------------------------------------------
# OAuth2 login for Swagger Authorize
# --------------------------------------------------

@router.post(
    f"{settings.api_v1_prefix}/auth/token",
    response_model=TokenResponse,
)
def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    normalized_email = form_data.username.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            form_data.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
    }
