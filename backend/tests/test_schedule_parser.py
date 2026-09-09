from pathlib import Path

import pandas as pd

from app.services.schedule_parser import read_schedule_file


def test_schedule_parser_normalizes_csv(tmp_path: Path):
    source = tmp_path / "schedule.csv"
    pd.DataFrame([
        {
            "Activity ID": "PIPING-L5-001",
            "Activity Name": "Spool erection and installation Line 24-XX",
            "WBS": "1.2.3",
            "Discipline": "Piping",
            "Planned Start": "2026-09-01",
            "Planned Finish": "2026-09-10",
            "Planned %": "25%",
        }
    ]).to_csv(source, index=False)

    activities, errors = read_schedule_file(source)

    assert errors == []
    assert len(activities) == 1
    assert activities[0]["activity_id"] == "PIPING-L5-001"
    assert activities[0]["discipline"] == "Piping"
    assert activities[0]["planned_progress"] == 25.0
    assert activities[0]["planned_start"] == "2026-09-01"


def test_schedule_parser_reports_missing_required_column(tmp_path: Path):
    source = tmp_path / "bad.csv"
    pd.DataFrame([{"Description": "Something"}]).to_csv(source, index=False)

    try:
        read_schedule_file(source)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Activity ID" in str(exc)
