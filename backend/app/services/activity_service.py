"""Firestore operations for schedule activities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.database.firestore import get_firestore_client

COLLECTION = "activities"


def _serialize(data: dict[str, Any], activity_doc_id: str) -> dict[str, Any]:
    result = dict(data)
    result["id"] = activity_doc_id
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result


def list_activities(project_id: str, limit: int = 500) -> list[dict[str, Any]]:
    client = get_firestore_client()
    query = (
        client.collection(COLLECTION)
        .where("project_id", "==", project_id)
        .limit(limit)
    )
    docs = list(query.stream())
    docs.sort(key=lambda d: (d.to_dict() or {}).get("activity_id", ""))
    return [_serialize(doc.to_dict() or {}, doc.id) for doc in docs]


def import_activities(project_id: str, activities: list[dict[str, Any]]) -> int:
    client = get_firestore_client()
    now = datetime.now(timezone.utc)
    imported = 0

    # Deterministic document IDs make re-importing the same Activity ID update
    # the existing activity instead of creating duplicates.
    batch = client.batch()
    operations = 0

    for activity in activities:
        safe_id = f"{project_id}__{activity['activity_id']}".replace("/", "_")
        ref = client.collection(COLLECTION).document(safe_id)
        data = dict(activity)
        data.update({
            "project_id": project_id,
            "updated_at": now,
        })
        snapshot = ref.get()
        if not snapshot.exists:
            data["created_at"] = now
        batch.set(ref, data, merge=True)
        imported += 1
        operations += 1

        if operations == 450:
            batch.commit()
            batch = client.batch()
            operations = 0

    if operations:
        batch.commit()

    return imported


def ensure_project_exists(project_id: str) -> None:
    client = get_firestore_client()
    ref = client.collection("projects").document(project_id)
    if not ref.get().exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
