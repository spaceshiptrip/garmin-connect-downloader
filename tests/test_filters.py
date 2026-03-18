from datetime import date

from garmin_activity_downloader import matches_interval, matches_sport


def test_matches_interval_every_day():
    assert matches_interval(date(2025, 10, 1), "every_day", date(2025, 10, 1))


def test_matches_interval_wednesday():
    assert matches_interval(date(2025, 10, 1), "wednesday", date(2025, 10, 1))
    assert not matches_interval(date(2025, 10, 2), "wednesday", date(2025, 10, 1))


def test_matches_interval_all_tuesdays():
    assert matches_interval(date(2025, 10, 7), "all_tuesdays", date(2025, 10, 1))
    assert not matches_interval(date(2025, 10, 8), "all_tuesdays", date(2025, 10, 1))


def test_matches_interval_every_other_day():
    anchor = date(2025, 10, 1)
    assert matches_interval(date(2025, 10, 1), "every_other_day", anchor)
    assert not matches_interval(date(2025, 10, 2), "every_other_day", anchor)
    assert matches_interval(date(2025, 10, 3), "every_other_day", anchor)


def test_matches_sport_running():
    activity = {"activityType": {"typeKey": "running"}, "activityName": "Base Run"}
    assert matches_sport(activity, "running")
    assert not matches_sport(activity, "hiking")


def test_matches_sport_trail_running_by_type():
    activity = {"activityType": {"typeKey": "trail_running"}, "activityName": "Morning Trail"}
    assert matches_sport(activity, "trail_running")


def test_matches_sport_trail_running_by_name():
    activity = {"activityType": {"typeKey": "running"}, "activityName": "Trail Run at Baldy"}
    assert matches_sport(activity, "trail_running")


def test_matches_sport_any():
    activity = {"activityType": {"typeKey": "pickleball"}, "activityName": "Glendale Pickleball"}
    assert matches_sport(activity, "any")
