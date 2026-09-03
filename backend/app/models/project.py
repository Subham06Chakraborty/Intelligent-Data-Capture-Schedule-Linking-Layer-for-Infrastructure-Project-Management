"""Pydantic models for project CRUD."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    location: str = Field(default="", max_length=200)
    project_type: str = Field(default="", max_length=200)
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    overall_progress: float = Field(default=0, ge=0, le=100)
    status: str = Field(default="planned", max_length=30)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValueError("finish_date cannot be before start_date")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    location: Optional[str] = Field(default=None, max_length=200)
    project_type: Optional[str] = Field(default=None, max_length=200)
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    overall_progress: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[str] = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValueError("finish_date cannot be before start_date")
        return self


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
