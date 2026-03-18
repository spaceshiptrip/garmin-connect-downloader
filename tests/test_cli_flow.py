from pathlib import Path

import garmin_activity_downloader as gad


class FakeClient:
    class ActivityDownloadFormat:
        GPX = "GPX"

    def __init__(self):
        self.downloaded = []

    def get_activities(self, start, limit):
        if start > 0:
            return []
        return [
            {
                "activityId": 1,
                "activityName": "Morning Run",
                "activityType": {"typeKey": "running"},
                "distance": 1609.344,
                "duration": 600,
                "elevationGain": 50,
                "startTimeLocal": "2025-10-07T06:30:00",
            },
            {
                "activityId": 2,
                "activityName": "Thursday Hike",
                "activityType": {"typeKey": "hiking"},
                "distance": 3218.688,
                "duration": 1800,
                "elevationGain": 200,
                "startTimeLocal": "2025-10-09T06:30:00",
            },
        ]

    def download_activity(self, activity_id, dl_fmt):
        self.downloaded.append((activity_id, dl_fmt))
        return b"<gpx></gpx>"


def test_main_list_only(monkeypatch, tmp_path: Path):
    fake = FakeClient()

    monkeypatch.setattr(gad, "init_client", lambda: fake)
    monkeypatch.setattr(
        "sys.argv",
        [
            "garmin_activity_downloader.py",
            "--start-date",
            "2025-10-01",
            "--interval",
            "all_tuesdays",
            "--sport",
            "running",
            "--download-format",
            "gpx",
            "--output-dir",
            str(tmp_path / "out"),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--summary-csv",
            str(tmp_path / "summary.csv"),
            "--list-only",
        ],
    )

    rc = gad.main()
    assert rc == 0
    assert fake.downloaded == []
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "summary.csv").exists()


def test_main_download(monkeypatch, tmp_path: Path):
    fake = FakeClient()

    monkeypatch.setattr(gad, "init_client", lambda: fake)
    monkeypatch.setattr(
        "sys.argv",
        [
            "garmin_activity_downloader.py",
            "--start-date",
            "2025-10-01",
            "--interval",
            "all_tuesdays",
            "--sport",
            "running",
            "--download-format",
            "gpx",
            "--output-dir",
            str(tmp_path / "out"),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--summary-csv",
            str(tmp_path / "summary.csv"),
        ],
    )

    rc = gad.main()
    assert rc == 0
    assert fake.downloaded == [(1, "GPX")]
    files = list((tmp_path / "out").glob("*.gpx"))
    assert len(files) == 1
