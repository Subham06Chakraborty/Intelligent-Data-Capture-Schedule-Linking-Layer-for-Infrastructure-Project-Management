from rapidfuzz import fuzz, process
import numpy as np
from typing import Optional
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Optional: Sentence Transformers for semantic matching
# Install: pip install sentence-transformers
# Falls back to fuzzy-only if not installed
# ─────────────────────────────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    _semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    SEMANTIC_AVAILABLE = True
    print("[FuzzyService] OK: Semantic matching enabled (sentence-transformers)")
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("[FuzzyService] WARN: sentence-transformers not installed. Using fuzzy-only mode.")


# ─────────────────────────────────────────────────────────────────────────────
# MATCH THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
THRESHOLD_AUTO_MATCH = 0.75    # >= 75% → auto-linked ✅
THRESHOLD_FLAG = 0.50          # 50–74% → flagged for planner review ⚠️
                               # <  50% → unmatched / new activity ❌


# ─────────────────────────────────────────────────────────────────────────────
# CORE MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def smart_match(
    extracted_activity: str,
    discipline: str,
    schedule_items: list[dict],
    use_semantic: bool = True,
) -> dict:
    """
    Hybrid semantic + fuzzy matching engine.

    Priority:
    1. Semantic similarity (sentence-transformers) — understands MEANING
       e.g. "spool erected" ≈ "pipe section installed"
    2. Fuzzy string match (RapidFuzz) — catches exact keyword overlaps
    3. Weighted combination: 60% semantic + 40% fuzzy

    Args:
        extracted_activity: Activity description from LLM extraction
        discipline: e.g. "piping"
        schedule_items: List of dicts with keys: activity_id, activity_desc, discipline
        use_semantic: Set False to force fuzzy-only (e.g. in tests)

    Returns dict with:
        status: "matched" | "flagged" | "unmatched"
        confidence: float 0.0–1.0
        matched_activity_id: str or None
        matched_description: str or None
        match_method: "semantic+fuzzy" | "fuzzy_only"
    """
    if not schedule_items:
        return _no_match_result("No schedule items provided")

    # ── Step 1: Filter by discipline (reduces search space + false positives)
    discipline_items = [
        item for item in schedule_items
        if item.get("discipline", "").lower() == discipline.lower()
    ]
    # If discipline filter leaves nothing, fall back to full schedule
    candidates = discipline_items if discipline_items else schedule_items

    descriptions = [c["activity_desc"] for c in candidates]
    ids = [c["activity_id"] for c in candidates]

    # ── Step 2: Semantic similarity scores
    if use_semantic and SEMANTIC_AVAILABLE and len(descriptions) > 0:
        try:
            extracted_emb = _semantic_model.encode([extracted_activity])
            candidate_embs = _semantic_model.encode(descriptions)
            semantic_scores = cosine_similarity(extracted_emb, candidate_embs)[0]
        except Exception:
            semantic_scores = np.zeros(len(descriptions))
    else:
        semantic_scores = np.zeros(len(descriptions))

    # ── Step 3: Fuzzy string scores
    fuzzy_scores = np.array([
        fuzz.token_sort_ratio(extracted_activity.lower(), d.lower()) / 100.0
        for d in descriptions
    ])

    # ── Step 4: Weighted combination
    if SEMANTIC_AVAILABLE and use_semantic:
        final_scores = 0.60 * semantic_scores + 0.40 * fuzzy_scores
        method = "semantic+fuzzy"
    else:
        final_scores = fuzzy_scores
        method = "fuzzy_only"

    best_idx = int(np.argmax(final_scores))
    best_score = float(final_scores[best_idx])

    # ── Step 5: Classify based on thresholds
    if best_score >= THRESHOLD_AUTO_MATCH:
        status = "matched"
    elif best_score >= THRESHOLD_FLAG:
        status = "flagged"
    else:
        status = "unmatched"

    return {
        "status": status,
        "confidence": round(best_score, 4),
        "matched_activity_id": ids[best_idx] if status != "unmatched" else None,
        "matched_description": descriptions[best_idx] if status != "unmatched" else None,
        "match_method": method,
        "discipline_filtered": len(discipline_items) > 0,
    }


def batch_match(
    extracted_activities: list[dict],
    schedule_items: list[dict],
) -> list[dict]:
    """
    Match a list of extracted activities against the schedule in one call.
    Returns the extracted activities enriched with match results.
    """
    enriched = []
    for activity in extracted_activities:
        match_result = smart_match(
            extracted_activity=activity.get("extracted_activity", ""),
            discipline=activity.get("discipline", ""),
            schedule_items=schedule_items,
        )
        enriched.append({**activity, **match_result})
    return enriched


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _no_match_result(reason: str = "") -> dict:
    return {
        "status": "unmatched",
        "confidence": 0.0,
        "matched_activity_id": None,
        "matched_description": None,
        "match_method": "none",
        "reason": reason,
    }


def get_match_summary(matched_activities: list[dict]) -> dict:
    """Returns counts for dashboard display."""
    total = len(matched_activities)
    matched = sum(1 for a in matched_activities if a.get("status") == "matched")
    flagged = sum(1 for a in matched_activities if a.get("status") == "flagged")
    unmatched = sum(1 for a in matched_activities if a.get("status") == "unmatched")
    avg_confidence = (
        round(
            sum(a.get("confidence", 0) for a in matched_activities) / total, 3
        )
        if total > 0
        else 0.0
    )

    return {
        "total": total,
        "matched": matched,
        "flagged": flagged,
        "unmatched": unmatched,
        "avg_confidence": avg_confidence,
        "match_rate_pct": round((matched / total) * 100, 1) if total > 0 else 0,
    }
