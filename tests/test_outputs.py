import json
from pathlib import Path

from garmin_activity_downloader import write_manifest, write_csv_summary


def test_write_manifest(tmp_path: Path):
    path = tmp_path / "manifest.json"
    payload = {"matched_count": 2, "downloaded_count": 1}
    write_manifest(path, payload)

    assert path.exists()
    data = json.loads(path.read_text())
    assert data["matched_count"] == 2
    assert data["downloaded_count"] == 1


def test_write_csv_summary(tmp_path: Path):
    path = tmp_path / "summary.csv"
    activities = [
        {
            "activityId": 123,
            "activityName": "Morning Run",
            "activityType": {"typeKey": "running"},
            "distance": 1609.344,
            "duration": 600,
            "elevationGain": 50,
            "startTimeLocal": "2025-10-07T06:30:00",
        }
    ]

    write_csv_summary(path, activities)

    text = path.read_text()
    assert "activity_id" in text
    assert "Morning Run" in text
    assert "running" in text
