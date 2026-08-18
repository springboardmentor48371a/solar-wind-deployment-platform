import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProjectStatus = Literal["Planning", "Analysis", "Completed"]


class ProjectOwnerResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    region: str = Field(..., min_length=1, max_length=100)
    project_status: ProjectStatus = "Planning"


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    region: str | None = Field(default=None, min_length=1, max_length=100)
    project_status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    description: str | None
    region: str
    project_status: str
    created_by: uuid.UUID
    owner: ProjectOwnerResponse
    created_at: datetime
    updated_at: datetime
