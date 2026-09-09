"""Pydantic models for schedule activity import and retrieval."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ActivityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    project_id: str
    activity_id: str
    activity_name: str
    activity_desc: str = ""
    wbs_code: str = ""
    wbs_level: Optional[int] = None
    discipline: str = ""
    contractor: str = ""
    region: str = ""
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    planned_progress: float = Field(default=0, ge=0, le=100)


class ScheduleImportResponse(BaseModel):
    project_id: str
    filename: str
    rows_read: int
    imported: int
    skipped: int
    errors: list[str] = []
