from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreate(BaseModel):
    title: str = Field(
        default="Untitled Resume",
        min_length=1,
        max_length=150,
    )
    target_job: str | None = Field(default=None, max_length=150)
    resume_data: dict[str, Any] = Field(default_factory=dict)


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    target_job: str | None
    resume_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
