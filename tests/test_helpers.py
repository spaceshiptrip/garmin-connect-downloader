from datetime import date

from garmin_activity_downloader import parse_ymd, safe_name, make_filename


def test_parse_ymd():
    assert parse_ymd("2025-10-01") == date(2025, 10, 1)


def test_safe_name_basic():
    assert safe_name("La Canada Flintridge Hiking") == "La_Canada_Flintridge_Hiking"


def test_safe_name_strips_extra_chars():
    assert safe_name("  weird / name: test  ") == "weird_name_test"


def test_make_filename():
    activity = {
        "activityId": 12345,
        "activityName": "Morning Run",
        "activityType": {"typeKey": "running"},
        "startTimeLocal": "2025-10-07T06:30:00",
    }
    got = make_filename(activity, "gpx")
    assert got == "2025-10-07_Morning_Run_running_12345.gpx"
