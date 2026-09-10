import uuid
from datetime import datetime
from typing import Optional
from app.database.firestore import get_db


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT SERVICE — Full traceability on every activity state change
# ─────────────────────────────────────────────────────────────────────────────

VALID_ACTIONS = {
    "auto_extracted",
    "llm_matched",
    "fuzzy_matched",
    "semantic_matched",
    "planner_confirmed",
    "planner_rejected",
    "planner_reassigned",
    "prediction_generated",
    "memory_updated",
}


async def log_action(
    activity_id: str,
    action: str,
    performed_by: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    confidence: Optional[float] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Log a single audit event to Firestore.
    Returns the audit_id of the created record.
    """
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Must be one of: {VALID_ACTIONS}")

    audit_id = str(uuid.uuid4())
    entry = {
        "audit_id": audit_id,
        "activity_id": activity_id,
        "action": action,
        "performed_by": performed_by,
        "timestamp": datetime.utcnow().isoformat(),
        "old_value": old_value or {},
        "new_value": new_value or {},
        "confidence": confidence,
        "notes": notes or "",
    }

    db = get_db()
    db.collection("audit_trail").document(audit_id).set(entry)
    return audit_id


async def get_audit_trail(activity_id: str) -> list[dict]:
    """
    Retrieve full audit history for an activity, sorted by timestamp asc.
    """
    db = get_db()
    docs = (
        db.collection("audit_trail")
        .where("activity_id", "==", activity_id)
        .order_by("timestamp")
        .stream()
    )
    return [doc.to_dict() for doc in docs]


async def get_recent_audit_log(limit: int = 50) -> list[dict]:
    """
    Get the most recent audit entries across all activities.
    Used for the admin audit log view.
    """
    db = get_db()
    docs = (
        db.collection("audit_trail")
        .order_by("timestamp", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]
