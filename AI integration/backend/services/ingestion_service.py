import io
import pandas as pd
import pdfplumber
from datetime import datetime
from typing import Tuple
from app.services.llm_service import extract_activities_from_text, summarize_report


# ─────────────────────────────────────────────────────────────────────────────
# FILE PARSERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """
    Extract all text from a PDF file.
    Returns: (raw_text, report_date_str)
    """
    full_text = ""
    report_date = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        # Try to extract date from first 200 chars
        import re
        date_match = re.search(
            r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}\-\d{2}\-\d{2})\b",
            full_text[:200],
        )
        if date_match:
            report_date = date_match.group(1)

    except Exception as e:
        print(f"[PARSE ERROR] PDF parsing failed: {e}")

    return full_text.strip(), report_date


def parse_excel(file_bytes: bytes) -> list[dict]:
    """
    Parse a discipline spreadsheet (Excel/CSV) into normalised row dicts.
    Handles multiple common column naming conventions used in Indian EPC projects.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            print(f"[PARSE ERROR] Excel/CSV parsing failed: {e}")
            return []

    # Normalize column names — handles variations in Indian EPC spreadsheets
    col_map = {
        # Activity description variations
        "activity": "activity_desc",
        "activity description": "activity_desc",
        "work description": "activity_desc",
        "description": "activity_desc",
        "item": "activity_desc",
        "work done": "activity_desc",
        # Discipline
        "discipline": "discipline",
        "dept": "discipline",
        "department": "discipline",
        # Start date
        "start date": "actual_start",
        "actual start": "actual_start",
        "date started": "actual_start",
        "commenced": "actual_start",
        # End date
        "end date": "actual_end",
        "actual end": "actual_end",
        "completion date": "actual_end",
        "date completed": "actual_end",
        "finished": "actual_end",
        # Status
        "status": "status",
        "progress": "completion_percent",
        "% complete": "completion_percent",
        "percent complete": "completion_percent",
    }

    df.columns = [col_map.get(c.strip().lower(), c.strip().lower()) for c in df.columns]
    df = df.dropna(how="all")

    return df.to_dict(orient="records")


def parse_text(raw_text: str) -> Tuple[str, str]:
    """Pass-through for plain text input."""
    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    return raw_text.strip(), report_date


# ─────────────────────────────────────────────────────────────────────────────
# MAIN INGESTION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_file(file_bytes: bytes, filename: str, project_id: str) -> dict:
    """
    Full ingestion pipeline for uploaded files.
    1. Parse file based on type
    2. Extract activities via LLM
    3. Return raw extracted activities (fuzzy matching done separately)
    """
    ext = filename.lower().split(".")[-1]
    start_time = datetime.utcnow()

    if ext == "pdf":
        raw_text, report_date = parse_pdf(file_bytes)
        source_type = "pdf"
        activities_raw = extract_activities_from_text(raw_text, report_date)
        summary = summarize_report(raw_text[:2000])  # summarize first 2000 chars

    elif ext in ("xlsx", "xls"):
        rows = parse_excel(file_bytes)
        # Convert spreadsheet rows to text for LLM extraction
        rows_text = "\n".join(
            [
                f"Activity: {r.get('activity_desc', '')} | "
                f"Discipline: {r.get('discipline', '')} | "
                f"Start: {r.get('actual_start', '')} | "
                f"End: {r.get('actual_end', '')} | "
                f"Progress: {r.get('completion_percent', '')}%"
                for r in rows
                if r.get("activity_desc")
            ]
        )
        report_date = datetime.utcnow().strftime("%Y-%m-%d")
        source_type = "excel"
        activities_raw = extract_activities_from_text(rows_text, report_date)
        summary = f"Excel spreadsheet with {len(rows)} rows parsed."

    elif ext in ("txt", "text"):
        raw_text, report_date = parse_text(file_bytes.decode("utf-8", errors="ignore"))
        source_type = "text"
        activities_raw = extract_activities_from_text(raw_text, report_date)
        summary = summarize_report(raw_text[:2000])

    else:
        return {
            "error": f"Unsupported file type: {ext}",
            "supported": ["pdf", "xlsx", "xls", "txt"],
        }

    processing_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

    return {
        "source_type": source_type,
        "project_id": project_id,
        "filename": filename,
        "report_date": report_date,
        "summary": summary,
        "activities_raw": activities_raw,
        "total_extracted": len(activities_raw),
        "processing_time_ms": round(processing_ms, 1),
    }
