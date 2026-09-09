"""Parse Primavera/MS Project-style CSV/XLSX/XLS files into normalized activities."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

COLUMN_ALIASES = {
    "activity_id": ["activity_id", "activity id", "activity code", "id", "task id"],
    "activity_name": ["activity_name", "activity name", "activity", "task name", "task"],
    "activity_desc": ["activity_desc", "activity description", "description", "desc"],
    "wbs_code": ["wbs", "wbs code", "wbs_code", "wbs path"],
    "wbs_level": ["wbs_level", "wbs level", "level"],
    "discipline": ["discipline", "discipline name", "trade"],
    "contractor": ["contractor", "subcontractor", "vendor"],
    "region": ["region", "location", "site"],
    "planned_start": ["planned_start", "planned start", "start", "start date", "planned start date"],
    "planned_end": ["planned_end", "planned end", "finish", "finish date", "planned finish", "planned finish date"],
    "planned_progress": ["planned_progress", "planned %", "planned percent", "progress", "% complete", "percent complete"],
}


def _clean_column(value: Any) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def _column_map(columns) -> dict[str, str]:
    normalized = {_clean_column(c): c for c in columns}
    result: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if _clean_column(alias) in normalized:
                result[target] = normalized[_clean_column(alias)]
                break
    return result


def _parse_date(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def _parse_progress(value: Any) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    text = str(value).strip().replace("%", "")
    try:
        number = float(text)
    except ValueError:
        return 0.0
    # Accept either 0-100 or 0-1 representations.
    if 0 <= number <= 1 and "." in text:
        number *= 100
    return max(0.0, min(100.0, number))


def _parse_wbs_level(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        match = __import__("re").search(r"(\d+)", str(value))
        return int(match.group(1)) if match else None


def read_schedule_file(path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read a schedule file and return normalized activity dictionaries."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    else:
        raise ValueError("Unsupported schedule format. Use CSV, XLSX, or XLS.")

    frame = frame.dropna(how="all")
    mapping = _column_map(frame.columns)

    if "activity_id" not in mapping:
        raise ValueError("Missing required Activity ID column.")
    if "activity_name" not in mapping and "activity_desc" not in mapping:
        raise ValueError("Missing required Activity Name/Description column.")

    activities: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, row in frame.iterrows():
        row_number = int(index) + 2
        activity_id = str(row.get(mapping["activity_id"], "")).strip()
        activity_name = str(
            row.get(mapping.get("activity_name", mapping.get("activity_desc")), "")
        ).strip()
        if not activity_id or activity_id.lower() == "nan":
            errors.append(f"Row {row_number}: missing Activity ID; skipped.")
            continue
        if not activity_name or activity_name.lower() == "nan":
            errors.append(f"Row {row_number}: missing Activity Name/Description; skipped.")
            continue

        activity_desc = ""
        if "activity_desc" in mapping:
            raw_desc = row.get(mapping["activity_desc"], "")
            activity_desc = "" if pd.isna(raw_desc) else str(raw_desc).strip()

        activities.append({
            "activity_id": activity_id,
            "activity_name": activity_name,
            "activity_desc": activity_desc,
            "wbs_code": str(row.get(mapping["wbs_code"], "")).strip()
                if "wbs_code" in mapping and not pd.isna(row.get(mapping["wbs_code"])) else "",
            "wbs_level": _parse_wbs_level(row.get(mapping["wbs_level"])) if "wbs_level" in mapping else None,
            "discipline": str(row.get(mapping["discipline"], "")).strip()
                if "discipline" in mapping and not pd.isna(row.get(mapping["discipline"])) else "",
            "contractor": str(row.get(mapping["contractor"], "")).strip()
                if "contractor" in mapping and not pd.isna(row.get(mapping["contractor"])) else "",
            "region": str(row.get(mapping["region"], "")).strip()
                if "region" in mapping and not pd.isna(row.get(mapping["region"])) else "",
            "planned_start": _parse_date(row.get(mapping["planned_start"])) if "planned_start" in mapping else None,
            "planned_end": _parse_date(row.get(mapping["planned_end"])) if "planned_end" in mapping else None,
            "planned_progress": _parse_progress(row.get(mapping["planned_progress"])) if "planned_progress" in mapping else 0.0,
        })

    return activities, errors
