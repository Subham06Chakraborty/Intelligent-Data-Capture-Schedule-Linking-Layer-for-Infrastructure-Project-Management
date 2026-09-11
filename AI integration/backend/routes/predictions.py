from fastapi import APIRouter, Query, HTTPException
from app.services.predictions_service import predict_delay_risk, calculate_roi
from app.database.firestore import get_db
from collections import defaultdict
from datetime import datetime

router = APIRouter(prefix="/analytics")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/delay-prediction
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/delay-prediction", summary="Predict delay risk for a specific activity")
async def delay_prediction(activity_id: str = Query(...)):
    db = get_db()
    doc = db.collection("progress_events").document(activity_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = doc.to_dict()
    result = predict_delay_risk(activity)

    # Save prediction back to activity document
    db.collection("progress_events").document(activity_id).update({"prediction": result})
    return {"activity_id": activity_id, **result}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/discipline-summary
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/discipline-summary", summary="Discipline-wise delay rate and performance stats")
async def discipline_summary(project_id: str = Query(...)):
    db = get_db()
    docs = db.collection("progress_events").where("project_id", "==", project_id).stream()
    activities = [doc.to_dict() for doc in docs]

    summary = defaultdict(lambda: {"total": 0, "matched": 0, "flagged": 0, "unmatched": 0,
                                    "high_risk": 0, "avg_confidence": []})

    for a in activities:
        d = a.get("discipline", "unknown")
        summary[d]["total"] += 1
        status = a.get("status", "unmatched")
        summary[d][status] = summary[d].get(status, 0) + 1
        summary[d]["avg_confidence"].append(a.get("confidence", 0))

        risk = a.get("prediction", {}).get("risk_level", "LOW")
        if risk == "HIGH":
            summary[d]["high_risk"] += 1

    result = []
    for discipline, data in summary.items():
        confs = data.pop("avg_confidence")
        data["avg_confidence"] = round(sum(confs) / len(confs), 3) if confs else 0
        result.append({"discipline": discipline, **data})

    return {"project_id": project_id, "disciplines": result}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/weekly-trend
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/weekly-trend", summary="Weekly activity ingestion trend (matched/flagged/unmatched)")
async def weekly_trend(project_id: str = Query(...)):
    db = get_db()
    docs = db.collection("progress_events").where("project_id", "==", project_id).stream()

    weekly = defaultdict(lambda: {"matched": 0, "flagged": 0, "unmatched": 0})
    for doc in docs:
        a = doc.to_dict()
        ingested = a.get("ingested_at", "")
        if ingested:
            try:
                dt = datetime.fromisoformat(ingested.replace("Z", "+00:00"))
                week_key = dt.strftime("%Y-W%V")
                status = a.get("status", "unmatched")
                weekly[week_key][status] += 1
            except Exception:
                pass

    trend = [{"week": k, **v} for k, v in sorted(weekly.items())]
    return {"project_id": project_id, "trend": trend}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/institutional-memory
# THE KILLER FEATURE — queryable historical patterns
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/institutional-memory", summary="Historical patterns for future project planning")
async def institutional_memory(
    discipline: str = Query(default=None),
    activity_type: str = Query(default=None),
    limit: int = Query(default=20, le=100),
):
    db = get_db()
    query = db.collection("institutional_memory")

    if discipline:
        query = query.where("discipline", "==", discipline)
    if activity_type:
        query = query.where("activity_type", "==", activity_type)

    docs = query.limit(limit).stream()
    memories = [doc.to_dict() for doc in docs]

    # Compute aggregated insights
    if memories:
        avg_overrun = sum(m.get("overrun_days", 0) for m in memories) / len(memories)
        delay_causes = defaultdict(int)
        for m in memories:
            cause = m.get("delay_cause")
            if cause:
                delay_causes[cause] += 1
        top_cause = max(delay_causes, key=delay_causes.get) if delay_causes else "Unknown"
    else:
        avg_overrun = 0
        top_cause = "No data yet"

    return {
        "total_records": len(memories),
        "insights": {
            "avg_overrun_days": round(avg_overrun, 1),
            "most_common_delay_cause": top_cause,
            "data_message": (
                f"Based on {len(memories)} logged activities. "
                "Every activity you log makes future predictions more accurate."
                if memories else "No historical data yet. Start logging to build institutional memory."
            ),
        },
        "records": memories,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/roi-dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/roi-dashboard", summary="ROI and value dashboard for project management")
async def roi_dashboard(
    project_id: str = Query(...),
    project_budget_cr: float = Query(default=500.0),
):
    result = calculate_roi(project_id, project_budget_cr)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/analytics/model-metrics
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/model-metrics", summary="Get ML model performance metrics")
async def model_metrics():
    from app.services.predictions_service import get_model_metrics
    return get_model_metrics()

