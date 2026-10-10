from pydantic import BaseModel


class HomeResponse(BaseModel):
    message: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class InfoResponse(BaseModel):
    project: str
    backend: str
    version: str
    features: list[str]


from pydantic import BaseModel, Field


class ResumeRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    target_role: str = Field(min_length=2, max_length=100)
    skills: list[str] = Field(min_length=1, max_length=30)
