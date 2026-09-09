"""Schedule import and activity APIs."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.schedule import ActivityResponse, ScheduleImportResponse
from app.services import activity_service
from app.services.schedule_parser import read_schedule_file

router = APIRouter(prefix="/api/projects/{project_id}/schedule", tags=["Schedules"])

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads" / "schedules"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


@router.get("/activities", response_model=list[ActivityResponse])
def get_activities(project_id: str):
    activity_service.ensure_project_exists(project_id)
    return activity_service.list_activities(project_id)


@router.post("/import", response_model=ScheduleImportResponse, status_code=status.HTTP_201_CREATED)
async def import_schedule(project_id: str, file: UploadFile = File(...)):
    activity_service.ensure_project_exists(project_id)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload CSV, XLSX, or XLS.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Schedule file exceeds the 10 MB prototype limit.")

    safe_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = UPLOAD_DIR / safe_name
    stored_path.write_bytes(content)

    try:
        activities, parse_errors = read_schedule_file(stored_path)
    except ValueError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Could not read schedule file: {exc}") from exc

    if not activities:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No valid activities were found in the schedule.")

    imported = activity_service.import_activities(project_id, activities)

    return {
        "project_id": project_id,
        "filename": file.filename or safe_name,
        "rows_read": len(activities) + len(parse_errors),
        "imported": imported,
        "skipped": len(parse_errors),
        "errors": parse_errors[:20],
    }
