"""
routes/ai_activities.py
------------------------
AI progress event listing, detail, human review, and audit endpoints.

These routes operate on the `progress_events` collection — NOT `activities`.
The `activities` collection is the baseline schedule (read-only from here).

Routes:
  GET  /api/v1/activities/                    — List progress events (with filters)
  GET  /api/v1/activities/{event_id}          — Get single event + audit trail
  PUT  /api/v1/activities/{event_id}/review   — Planner confirm / reject / reassign
  GET  /api/v1/activities/{event_id}/audit    — Full audit trail for an event
"""

from fastapi import APIRouter, HTTPException, Query
from app.database.firestore import get_firestore_client as get_db
from app.services.audit_service import log_action, get_audit_trail

router = APIRouter(prefix="/activities")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/
# List all progress events with optional filters
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", summary="List all AI-extracted progress events")
async def list_activities(
    project_id: str = Query(...),
    discipline: str = Query(default=None),
    status: str = Query(default=None),   # matched / flagged / unmatched
    limit: int = Query(default=50, le=200),
):
    """
    Returns AI-extracted execution events from `progress_events`.
    Includes summary counts for matched / flagged / unmatched.
    """
    db = get_db()
    query = db.collection("progress_events").where("project_id", "==", project_id)

    if discipline:
        query = query.where("discipline", "==", discipline)
    if status:
        query = query.where("status", "==", status)

    docs = query.limit(limit).stream()
    events = [doc.to_dict() for doc in docs]

    total = len(events)
    counts = {
        "matched": sum(1 for e in events if e.get("status") == "matched"),
        "flagged": sum(1 for e in events if e.get("status") == "flagged"),
        "unmatched": sum(1 for e in events if e.get("status") == "unmatched"),
    }

    return {"total": total, "counts": counts, "activities": events}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/{event_id}
# Get a single progress event with full detail + audit trail
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{event_id}", summary="Get a single progress event with audit trail")
async def get_activity(event_id: str):
    db = get_db()
    doc = db.collection("progress_events").document(event_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Progress event not found")

    event = doc.to_dict()
    audit_trail = await get_audit_trail(event_id)
    return {**event, "audit_trail": audit_trail}


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/v1/activities/{event_id}/review
# Planner confirms, rejects, or reassigns a match
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{event_id}/review", summary="Planner confirms / rejects / reassigns a match")
async def review_activity(event_id: str, payload: dict):
    """
    Body: {
        "action": "confirm" | "reject" | "reassign",
        "matched_activity_id": str   (required if action == "reassign"),
        "notes": str,
        "reviewed_by": str
    }

    confirm   → sets status = matched
    reject    → sets status = unmatched, clears matched_activity_id
    reassign  → sets a new baseline activity link from the `activities` collection
    """
    action = payload.get("action")
    reviewed_by = payload.get("reviewed_by", "planner")

    if action not in ("confirm", "reject", "reassign"):
        raise HTTPException(status_code=400, detail="action must be confirm / reject / reassign")

    db = get_db()
    doc_ref = db.collection("progress_events").document(event_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Progress event not found")

    old_data = doc.to_dict()

    if action == "confirm":
        update = {
            "status": "matched",
            "planner_reviewed": True,
            "reviewed_by": reviewed_by,
        }
        audit_action = "planner_confirmed"

    elif action == "reject":
        update = {
            "status": "unmatched",
            "planner_reviewed": True,
            "reviewed_by": reviewed_by,
            "matched_activity_id": None,
            "matched_description": None,
        }
        audit_action = "planner_rejected"

    elif action == "reassign":
        new_match_id = payload.get("matched_activity_id")
        if not new_match_id:
            raise HTTPException(status_code=400, detail="matched_activity_id required for reassign")

        # Look up the new baseline activity description from activities collection
        schedule_doc = db.collection("activities").document(new_match_id).get()
        new_desc = (
            schedule_doc.to_dict().get("activity_name", "")
            if schedule_doc.exists
            else ""
        )
        update = {
            "status": "matched",
            "matched_activity_id": new_match_id,
            "matched_description": new_desc,
            "planner_reviewed": True,
            "reviewed_by": reviewed_by,
            "confidence": 1.0,   # planner manually confirmed → 100%
        }
        audit_action = "planner_reassigned"

    doc_ref.update(update)

    await log_action(
        activity_id=event_id,
        action=audit_action,
        performed_by=reviewed_by,
        old_value={"status": old_data.get("status")},
        new_value=update,
        notes=payload.get("notes"),
    )

    return {
        "event_id": event_id,
        "action": action,
        "status": "updated",
        "message": "Review saved successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/{event_id}/audit
# Full audit trail for a progress event
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{event_id}/audit", summary="Full audit trail for a progress event")
async def activity_audit(event_id: str):
    trail = await get_audit_trail(event_id)
    return {"event_id": event_id, "audit_trail": trail, "total_events": len(trail)}
