"""Firestore operations for projects."""
from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.database.firestore import get_firestore_client
from app.models.project import ProjectCreate, ProjectUpdate

COLLECTION = "projects"


def _serialize(data: dict[str, Any], project_id: str) -> dict[str, Any]:
    result = dict(data)
    result["id"] = project_id
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    for key in ("start_date", "finish_date"):
        value = result.get(key)
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result


def list_projects() -> list[dict[str, Any]]:
    client = get_firestore_client()
    docs = client.collection(COLLECTION).order_by("name").stream()
    return [_serialize(doc.to_dict() or {}, doc.id) for doc in docs]


def get_project(project_id: str) -> dict[str, Any]:
    client = get_firestore_client()
    doc = client.collection(COLLECTION).document(project_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _serialize(doc.to_dict() or {}, doc.id)


def create_project(payload: ProjectCreate) -> dict[str, Any]:
    client = get_firestore_client()
    now = datetime.now(timezone.utc)
    data = payload.model_dump(mode="json")
    data.update({"created_at": now, "updated_at": now})
    doc_ref = client.collection(COLLECTION).document()
    doc_ref.set(data)
    return _serialize(data, doc_ref.id)


def update_project(project_id: str, payload: ProjectUpdate) -> dict[str, Any]:
    client = get_firestore_client()
    doc_ref = client.collection(COLLECTION).document(project_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    updates = payload.model_dump(exclude_unset=True, mode="json")
    current = snapshot.to_dict() or {}
    if "start_date" in updates or "finish_date" in updates:
        start = updates.get("start_date", current.get("start_date"))
        finish = updates.get("finish_date", current.get("finish_date"))
        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(finish, str):
            finish = date.fromisoformat(finish)
        if start and finish and finish < start:
            raise HTTPException(status_code=422, detail="finish_date cannot be before start_date")
    updates["updated_at"] = datetime.now(timezone.utc)
    doc_ref.update(updates)
    current.update(updates)
    return _serialize(current, project_id)


def delete_project(project_id: str) -> None:
    client = get_firestore_client()
    doc_ref = client.collection(COLLECTION).document(project_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    doc_ref.delete()
