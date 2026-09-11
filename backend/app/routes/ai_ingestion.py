"""
routes/ai_ingestion.py
-----------------------
AI document ingestion endpoints:
  POST /api/v1/ingest/upload  — PDF / Excel / TXT report → extract + match
  POST /api/v1/ingest/chat    — Supervisor chat → conversational activity logging
  POST /api/v1/ingest/voice   — Voice note → Whisper → chat ingestion

IMPORTANT: Extracted execution events are stored in `progress_events` collection.
           The `activities` collection is reserved for baseline schedule activities only.
"""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.services.ingestion_service import ingest_file
from app.services.fuzzy_service import batch_match, get_match_summary, smart_match
from app.services.audit_service import log_action
from app.services.predictions_service import predict_delay_risk
from app.database.firestore import get_firestore_client as get_db


# ─────────────────────────────────────────────────────────────────────────────
# RBAC helper
# ─────────────────────────────────────────────────────────────────────────────
def check_rbac(supervisor: str, discipline: str) -> bool:
    """
    Checks if the supervisor is authorized to log for the given discipline.
    Admin / system / anonymous roles bypass RBAC.
    """
    if not supervisor or not discipline:
        return True

    sup_lower = supervisor.lower()
    disc_lower = discipline.lower()

    if "admin" in sup_lower or "system" in sup_lower or "anonymous" in sup_lower:
        return True

    known_disciplines = ["civil", "piping", "electrical", "instrumentation", "hse", "mechanical"]
    user_disciplines = [d for d in known_disciplines if d in sup_lower]

    if user_disciplines and disc_lower not in user_disciplines:
        return False

    return True


router = APIRouter(prefix="/ingest")


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ingest/upload
# Upload PDF / Excel / TXT report → auto-extract + match activities
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload", summary="Upload a site report (PDF / Excel / TXT)")
async def upload_report(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    uploaded_by: str = Form(default="system"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="File too large. Max 10 MB.")

    db = get_db()

    # ── Step 1: Parse file + LLM extraction ──────────────────────────────────
    result = ingest_file(file_bytes, file.filename, project_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # ── Step 2: Create progress_reports record ────────────────────────────────
    report_id = str(uuid.uuid4())
    report_doc = {
        "report_id": report_id,
        "project_id": project_id,
        "filename": file.filename,
        "source_type": result["source_type"],
        "uploaded_by": uploaded_by,
        "report_summary": result.get("summary", ""),
        "processing_time_ms": result.get("processing_time_ms", 0),
        "status": "processed",
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    db.collection("progress_reports").document(report_id).set(report_doc)

    # ── Step 3: Load baseline activities for this project from Firestore ──────
    # NOTE: activities collection = baseline schedule only (never overwrite it)
    schedule_docs = db.collection("activities").where("project_id", "==", project_id).stream()
    schedule_items = [doc.to_dict() for doc in schedule_docs]

    # ── Step 4: Fuzzy + Semantic matching ────────────────────────────────────
    enriched = batch_match(result["activities_raw"], schedule_items)

    # ── Step 5: Save each event to progress_events + predictions + audit ──────
    saved_events = []

    for act in enriched:
        event_id = str(uuid.uuid4())

        # Lookup matched baseline activity for accurate planned duration
        matched_activity = next(
            (
                item for item in schedule_items
                if item.get("activity_id") == act.get("matched_activity_id")
            ),
            None,
        )

        planned_days = 7  # safe default
        if matched_activity:
            try:
                planned_start = matched_activity.get("planned_start")
                planned_end = matched_activity.get("planned_end")
                if planned_start and planned_end:
                    start_date = datetime.fromisoformat(str(planned_start))
                    end_date = datetime.fromisoformat(str(planned_end))
                    planned_days = max((end_date - start_date).days, 1)
            except (ValueError, TypeError):
                planned_days = 7

        prediction = predict_delay_risk({
            "discipline": act.get(
                "discipline",
                matched_activity.get("discipline", "civil") if matched_activity else "civil"
            ),
            "planned_duration_days": planned_days,
            "wbs_level": matched_activity.get("wbs_level", 5) if matched_activity else 5,
            "contractor_score": matched_activity.get("contractor_score", 0.75) if matched_activity else 0.75,
            "resource_count": matched_activity.get("resource_count", 5) if matched_activity else 5,
        })

        # Store in progress_events — NOT in activities (baseline is sacred)
        event_doc = {
            "event_id": event_id,
            "report_id": report_id,
            "project_id": project_id,
            "ingested_by": uploaded_by,
            "source_type": result["source_type"],
            "filename": file.filename,
            **act,
            "prediction": prediction,
            "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        db.collection("progress_events").document(event_id).set(event_doc)

        # Audit entries
        await log_action(
            activity_id=event_id,
            action="auto_extracted",
            performed_by=uploaded_by,
            new_value={"match_status": act.get("status"), "confidence": act.get("confidence")},
            confidence=act.get("confidence"),
        )
        if act.get("status") in ("matched", "flagged"):
            await log_action(
                activity_id=event_id,
                action="semantic_matched" if "semantic" in act.get("match_method", "") else "fuzzy_matched",
                performed_by="system",
                new_value={"matched_id": act.get("matched_activity_id")},
                confidence=act.get("confidence"),
            )
        if prediction:
            await log_action(
                activity_id=event_id,
                action="prediction_generated",
                performed_by="system",
                new_value={"prediction": prediction},
            )

        saved_events.append(event_doc)

    summary = get_match_summary(enriched)

    return {
        "report_id": report_id,
        "filename": file.filename,
        "source_type": result["source_type"],
        "report_summary": result.get("summary", ""),
        "processing_time_ms": result["processing_time_ms"],
        **summary,
        "activities": saved_events,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ingest/chat
# Supervisor chat message → conversational activity logging
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/chat", summary="Supervisor chat interface for activity logging")
async def chat_ingest(payload: dict):
    """
    Body: { "message": str, "history": list, "project_id": str, "supervisor": str }
    Returns: { "reply": str, "activity_log": dict | null }
    """
    from app.services.llm_service import chat_with_supervisor

    message = payload.get("message", "").strip()
    history = payload.get("history", [])
    project_id = payload.get("project_id", "")
    supervisor = payload.get("supervisor", "anonymous")

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = chat_with_supervisor(message, history)

    # If LLM captured a complete activity, save it to progress_events
    if result.get("activity_log"):
        act = result["activity_log"]

        # ── RBAC security check ───────────────────────────────────────────────
        if not check_rbac(supervisor, act.get("discipline", "")):
            result["reply"] = (
                f"🚨 Security Alert: You are logged in as '{supervisor}' and are not "
                f"authorized to log activities for the '{act.get('discipline')}' discipline. "
                f"Submission blocked."
            )
            result["activity_log"] = None
            return result

        db = get_db()
        schedule_docs = db.collection("activities").where("project_id", "==", project_id).stream()
        schedule_items = [doc.to_dict() for doc in schedule_docs]

        match = smart_match(
            act.get("extracted_activity", ""),
            act.get("discipline", ""),
            schedule_items,
        )

        event_id = str(uuid.uuid4())
        event_doc = {
            "event_id": event_id,
            "project_id": project_id,
            "ingested_by": supervisor,
            "source_type": "chat",
            **act,
            **match,
            "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        db.collection("progress_events").document(event_id).set(event_doc)

        await log_action(
            activity_id=event_id,
            action="auto_extracted",
            performed_by=supervisor,
            new_value=event_doc,
            confidence=match.get("confidence"),
        )

        result["event_id"] = event_id
        result["match_result"] = match

    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ingest/voice
# Supervisor voice note → Whisper transcription → chat ingestion
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/voice", summary="Supervisor voice note for activity logging")
async def voice_ingest(
    audio_file: UploadFile = File(...),
    project_id: str = Form(...),
    supervisor: str = Form(default="anonymous"),
    history: str = Form(default="[]"),
):
    import os
    import json
    from app.services.llm_service import transcribe_audio

    # Save audio temporarily
    temp_path = f"temp_{uuid.uuid4()}_{audio_file.filename}"
    try:
        with open(temp_path, "wb") as f:
            f.write(await audio_file.read())

        transcript = transcribe_audio(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not transcript:
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")

    payload = {
        "message": transcript,
        "history": json.loads(history) if history else [],
        "project_id": project_id,
        "supervisor": supervisor,
    }

    chat_response = await chat_ingest(payload)

    return {
        "transcription": transcript,
        **chat_response,
    }
