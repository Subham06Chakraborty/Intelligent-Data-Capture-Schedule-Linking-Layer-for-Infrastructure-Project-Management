from fastapi import APIRouter, HTTPException, Query
from app.database.firestore import get_db
from app.services.audit_service import log_action, get_audit_trail

router = APIRouter(prefix="/activities")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/
# List all activities with optional filters
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", summary="List all extracted + linked activities")
async def list_activities(
    project_id: str = Query(...),
    discipline: str = Query(default=None),
    status: str = Query(default=None),   # matched / flagged / unmatched
    limit: int = Query(default=50, le=200),
):
    db = get_db()
    query = db.collection("progress_events").where("project_id", "==", project_id)

    if discipline:
        query = query.where("discipline", "==", discipline)
    if status:
        query = query.where("status", "==", status)

    docs = query.limit(limit).stream()
    activities = [doc.to_dict() for doc in docs]

    # Summary counts
    total = len(activities)
    counts = {
        "matched": sum(1 for a in activities if a.get("status") == "matched"),
        "flagged": sum(1 for a in activities if a.get("status") == "flagged"),
        "unmatched": sum(1 for a in activities if a.get("status") == "unmatched"),
    }

    return {"total": total, "counts": counts, "activities": activities}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/{activity_id}
# Get a single activity with full detail + audit trail
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{activity_id}", summary="Get a single activity with audit trail")
async def get_activity(activity_id: str):
    db = get_db()
    doc = db.collection("progress_events").document(activity_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = doc.to_dict()
    audit_trail = await get_audit_trail(activity_id)
    return {**activity, "audit_trail": audit_trail}


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/v1/activities/{activity_id}/review
# Planner confirms, rejects, or reassigns a match
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{activity_id}/review", summary="Planner confirms / rejects / reassigns a match")
async def review_activity(activity_id: str, payload: dict):
    """
    Body: {
        "action": "confirm" | "reject" | "reassign",
        "matched_activity_id": str (required if action == "reassign"),
        "notes": str,
        "reviewed_by": str
    }
    """
    action = payload.get("action")
    reviewed_by = payload.get("reviewed_by", "planner")

    if action not in ("confirm", "reject", "reassign"):
        raise HTTPException(status_code=400, detail="action must be confirm / reject / reassign")

    db = get_db()
    doc_ref = db.collection("progress_events").document(activity_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")

    old_data = doc.to_dict()

    if action == "confirm":
        update = {"status": "matched", "planner_reviewed": True, "reviewed_by": reviewed_by}
        audit_action = "planner_confirmed"

    elif action == "reject":
        update = {"status": "unmatched", "planner_reviewed": True, "reviewed_by": reviewed_by,
                  "matched_activity_id": None, "matched_description": None}
        audit_action = "planner_rejected"

    elif action == "reassign":
        new_match_id = payload.get("matched_activity_id")
        if not new_match_id:
            raise HTTPException(status_code=400, detail="matched_activity_id required for reassign")

        # Look up the new match description from activities
        activity_doc = db.collection("activities").document(new_match_id).get()
        new_desc = activity_doc.to_dict().get("activity_desc", "") if activity_doc.exists else ""
        update = {
            "status": "matched",
            "matched_activity_id": new_match_id,
            "matched_description": new_desc,
            "planner_reviewed": True,
            "reviewed_by": reviewed_by,
            "confidence": 1.0,    # planner manually confirmed → 100%
        }
        audit_action = "planner_reassigned"

    doc_ref.update(update)
    await log_action(
        activity_id=activity_id,
        action=audit_action,
        performed_by=reviewed_by,
        old_value={"status": old_data.get("status")},
        new_value=update,
        notes=payload.get("notes"),
    )

    return {
    "event_id": activity_id,
    "action": action,
    "status": "updated",
    "message": "Activity review saved",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/activities/{activity_id}/audit
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{activity_id}/audit", summary="Full audit trail for an activity")
async def activity_audit(activity_id: str):
    trail = await get_audit_trail(activity_id)
    return {
    "event_id": activity_id,
    "audit_trail": trail,
    "total_events": len(trail),
    }
