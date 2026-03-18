#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
import getpass
import json
import re
import sys
from typing import Any

from garminconnect import Garmin


# ----------------------------
# Auth
# ----------------------------

def init_client() -> Garmin:
    tokenstore = Path("~/.garminconnect").expanduser()

    # Try token login first
    try:
        client = Garmin()
        client.login(str(tokenstore))
        print("Logged in using saved token.")
        return client
    except Exception:
        pass

    # Interactive login fallback
    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    client = Garmin(email=email, password=password, return_on_mfa=True)
    result1, result2 = client.login()

    if result1 == "needs_mfa":
        mfa_code = input("Please enter your MFA code: ").strip()
        client.resume_login(result2, mfa_code)

    client.garth.dump(str(tokenstore))
    print("Logged in and saved new token.")
    return client


# ----------------------------
# Parsing helpers
# ----------------------------

def parse_ymd(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def today_local() -> date:
    return date.today()


def parse_activity_date(activity: dict[str, Any]) -> date | None:
    candidates = [
        activity.get("startTimeLocal"),
        activity.get("startTimeGMT"),
        activity.get("activityDate"),
        activity.get("summaryDTO", {}).get("startTimeLocal")
        if isinstance(activity.get("summaryDTO"), dict)
        else None,
        activity.get("summaryDTO", {}).get("startTimeGMT")
        if isinstance(activity.get("summaryDTO"), dict)
        else None,
    ]

    for value in candidates:
        if not value:
            continue
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except Exception:
            pass
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except Exception:
            pass
    return None


def safe_name(text: str | None) -> str:
    text = (text or "activity").strip()
    text = re.sub(r"[^\w\-\.]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:120] or "activity"


def get_activity_type_key(activity: dict[str, Any]) -> str:
    activity_type = activity.get("activityType")
    if isinstance(activity_type, dict):
        return str(activity_type.get("typeKey", "")).lower()
    if isinstance(activity_type, str):
        return activity_type.lower()
    return ""


def get_activity_name(activity: dict[str, Any]) -> str:
    return str(activity.get("activityName", "Unnamed Activity"))


def get_activity_id(activity: dict[str, Any]) -> int | None:
    activity_id = activity.get("activityId")
    try:
        return int(activity_id)
    except Exception:
        return None


def get_distance_miles(activity: dict[str, Any]) -> float | None:
    distance_m = activity.get("distance")
    if isinstance(distance_m, (int, float)):
        return round(distance_m / 1609.344, 2)
    return None


def get_duration_minutes(activity: dict[str, Any]) -> float | None:
    duration_s = activity.get("duration")
    if isinstance(duration_s, (int, float)):
        return round(duration_s / 60.0, 1)
    return None


def get_elevation_gain(activity: dict[str, Any]) -> float | None:
    gain = activity.get("elevationGain")
    if isinstance(gain, (int, float)):
        return round(float(gain), 1)
    summary = activity.get("summaryDTO")
    if isinstance(summary, dict):
        gain = summary.get("elevationGain")
        if isinstance(gain, (int, float)):
            return round(float(gain), 1)
    return None


# ----------------------------
# Interval filtering
# ----------------------------

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def matches_interval(d: date, interval: str, anchor: date) -> bool:
    interval = interval.lower()

    if interval == "every_day":
        return True

    if interval in WEEKDAY_MAP:
        return d.weekday() == WEEKDAY_MAP[interval]

    if interval == "all_tuesdays":
        return d.weekday() == 1

    if interval == "weekdays":
        return d.weekday() < 5

    if interval == "weekends":
        return d.weekday() >= 5

    delta_days = (d - anchor).days

    if interval == "every_other_day":
        return delta_days % 2 == 0

    if interval == "every_3_days":
        return delta_days % 3 == 0

    if interval == "every_7_days":
        return delta_days % 7 == 0

    raise ValueError(f"Unsupported interval: {interval}")


# ----------------------------
# Sport filtering
# ----------------------------

SPORT_ALIASES = {
    "any": None,
    "running": {"running"},
    "trail_running": {"trail_running", "running"},
    "hiking": {"hiking"},
    "walking": {"walking"},
    "cycling": {"cycling", "road_biking", "indoor_cycling", "mountain_biking"},
    "mountain_biking": {"mountain_biking"},
    "strength_training": {"strength_training"},
    "swimming": {"swimming", "lap_swimming", "open_water_swimming"},
    "pickleball": {"pickleball"},   
}


def matches_sport(activity: dict[str, Any], sport_filter: str) -> bool:
    sport_filter = sport_filter.lower()
    allowed = SPORT_ALIASES.get(sport_filter)
    if allowed is None:
        return True

    type_key = get_activity_type_key(activity)
    name = get_activity_name(activity).lower()

    if sport_filter == "trail_running":
        # Garmin often stores trail runs as trail_running, but sometimes plain running.
        # Bias toward keeping obvious trail activities.
        return type_key in allowed or ("trail" in name and "run" in name)

    if sport_filter == "pickleball":
        return type_key in allowed or "pickleball" in name

    return type_key in allowed

# ----------------------------
# Download format mapping
# ----------------------------

EXTENSION_MAP = {
    "gpx": "gpx",
    "tcx": "tcx",
    "fit": "fit",
    "original": "zip",
    "csv": "csv",
}

# The library exposes download_activity(..., dl_fmt=ActivityDownloadFormat.X).
# We map string options to likely enum names and resolve them at runtime.
ENUM_CANDIDATES = {
    "gpx": ("GPX",),
    "tcx": ("TCX",),
    "fit": ("FIT",),
    "original": ("ORIGINAL", "ORIGINAL_FILE"),
    "csv": ("CSV",),
}


def resolve_download_format_enum(client: Garmin, fmt: str):
    fmt = fmt.lower()
    enum_class = getattr(client, "ActivityDownloadFormat", None)
    if enum_class is None:
        raise RuntimeError("Garmin client does not expose ActivityDownloadFormat.")

    for candidate in ENUM_CANDIDATES[fmt]:
        if hasattr(enum_class, candidate):
            return getattr(enum_class, candidate)

    available = [x for x in dir(enum_class) if x.isupper()]
    raise RuntimeError(
        f"Could not resolve download format '{fmt}'. "
        f"Available enum values may be: {available}"
    )


# ----------------------------
# Data fetch
# ----------------------------

def fetch_candidate_activities(
    client: Garmin,
    start_date: date,
    end_date: date,
    fetch_limit: int,
) -> list[dict[str, Any]]:
    start = 0
    out: list[dict[str, Any]] = []

    while True:
        batch = client.get_activities(start, fetch_limit)
        if not batch:
            break

        stop_early = False

        for act in batch:
            act_date = parse_activity_date(act)
            if act_date is None:
                continue

            if act_date < start_date:
                stop_early = True
                break

            if start_date <= act_date <= end_date:
                out.append(act)

        if stop_early or len(batch) < fetch_limit:
            break

        start += fetch_limit

    return out


# ----------------------------
# Output helpers
# ----------------------------

def make_filename(
    activity: dict[str, Any],
    download_format: str,
) -> str:
    act_date = parse_activity_date(activity)
    activity_id = get_activity_id(activity)
    activity_name = get_activity_name(activity)
    activity_type = get_activity_type_key(activity) or "unknown"
    ext = EXTENSION_MAP[download_format.lower()]

    return (
        f"{act_date}_{safe_name(activity_name)}_{safe_name(activity_type)}_{activity_id}.{ext}"
    )


def write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_csv_summary(csv_path: Path, activities: list[dict[str, Any]]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "date",
                "activity_id",
                "activity_name",
                "activity_type",
                "distance_miles",
                "duration_minutes",
                "elevation_gain",
            ]
        )
        for act in activities:
            writer.writerow(
                [
                    parse_activity_date(act),
                    get_activity_id(act),
                    get_activity_name(act),
                    get_activity_type_key(act),
                    get_distance_miles(act),
                    get_duration_minutes(act),
                    get_elevation_gain(act),
                ]
            )


# ----------------------------
# CLI
# ----------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Garmin activities by date range, interval, sport, and file format."
    )

    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end-date",
        default=today_local().isoformat(),
        help="End date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--interval",
        default="every_day",
        choices=[
            "every_day",
            "all_tuesdays",
            "every_other_day",
            "every_3_days",
            "every_7_days",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "weekdays",
            "weekends",
        ],
        help="Date interval filter.",
    )
    parser.add_argument(
        "--sport",
        default="any",
        choices=sorted(SPORT_ALIASES.keys()),
        help="Sport/activity type filter.",
    )
    parser.add_argument(
        "--download-format",
        default="gpx",
        choices=["gpx", "tcx", "fit", "original", "csv"],
        help="Download/export format.",
    )
    parser.add_argument(
        "--output-dir",
        default="downloads",
        help="Directory to save downloaded files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list matching activities; do not download files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Garmin page size for get_activities(). Default: 100.",
    )
    parser.add_argument(
        "--manifest",
        default="download_manifest.json",
        help="Path to write JSON manifest.",
    )
    parser.add_argument(
        "--summary-csv",
        default="download_summary.csv",
        help="Path to write CSV summary.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    start_date = parse_ymd(args.start_date)
    end_date = parse_ymd(args.end_date)

    if end_date < start_date:
        print("Error: --end-date must be on or after --start-date.", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = init_client()

    print(
        f"Fetching candidate activities from {start_date} to {end_date} "
        f"(interval={args.interval}, sport={args.sport}, format={args.download_format})"
    )

    candidates = fetch_candidate_activities(
        client=client,
        start_date=start_date,
        end_date=end_date,
        fetch_limit=args.limit,
    )

    matched: list[dict[str, Any]] = []
    for act in candidates:
        act_date = parse_activity_date(act)
        if act_date is None:
            continue
        if not matches_interval(act_date, args.interval, start_date):
            continue
        if not matches_sport(act, args.sport):
            continue
        matched.append(act)

    matched.sort(
        key=lambda a: (
            parse_activity_date(a) or date.min,
            get_activity_id(a) or 0,
        )
    )

    print(f"Matched {len(matched)} activities.")

    for act in matched:
        print(
            f"{parse_activity_date(act)} | "
            f"{get_activity_name(act)} | "
            f"type={get_activity_type_key(act)} | "
            f"mi={get_distance_miles(act)} | "
            f"min={get_duration_minutes(act)} | "
            f"id={get_activity_id(act)}"
        )

    write_csv_summary(Path(args.summary_csv), matched)

    downloaded: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    if not args.list_only:
        dl_enum = resolve_download_format_enum(client, args.download_format)

        for act in matched:
            activity_id = get_activity_id(act)
            if activity_id is None:
                failed.append(
                    {
                        "activityId": None,
                        "date": str(parse_activity_date(act)),
                        "name": get_activity_name(act),
                        "error": "Missing activityId",
                    }
                )
                continue

            file_path = output_dir / make_filename(act, args.download_format)

            if file_path.exists() and not args.overwrite:
                print(f"Skipping existing: {file_path}")
                skipped.append(
                    {
                        "activityId": activity_id,
                        "date": str(parse_activity_date(act)),
                        "name": get_activity_name(act),
                        "file": str(file_path),
                    }
                )
                continue

            try:
                blob = client.download_activity(activity_id, dl_fmt=dl_enum)

                mode = "wb"
                if isinstance(blob, str):
                    data = blob.encode("utf-8")
                else:
                    data = blob

                with file_path.open(mode) as f:
                    f.write(data)

                print(f"Saved: {file_path}")
                downloaded.append(
                    {
                        "activityId": activity_id,
                        "date": str(parse_activity_date(act)),
                        "name": get_activity_name(act),
                        "type": get_activity_type_key(act),
                        "file": str(file_path),
                    }
                )
            except Exception as e:
                print(f"Failed: {activity_id} {get_activity_name(act)} -> {e}")
                failed.append(
                    {
                        "activityId": activity_id,
                        "date": str(parse_activity_date(act)),
                        "name": get_activity_name(act),
                        "type": get_activity_type_key(act),
                        "error": str(e),
                    }
                )

    manifest = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "interval": args.interval,
        "sport": args.sport,
        "download_format": args.download_format,
        "output_dir": str(output_dir),
        "matched_count": len(matched),
        "downloaded_count": len(downloaded),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "summary_csv": args.summary_csv,
        "matched": [
            {
                "activityId": get_activity_id(act),
                "date": str(parse_activity_date(act)),
                "name": get_activity_name(act),
                "type": get_activity_type_key(act),
                "distance_miles": get_distance_miles(act),
                "duration_minutes": get_duration_minutes(act),
                "elevation_gain": get_elevation_gain(act),
            }
            for act in matched
        ],
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
    }

    write_manifest(Path(args.manifest), manifest)

    print()
    print(f"Summary CSV: {args.summary_csv}")
    print(f"Manifest:    {args.manifest}")
    print(f"Matched:     {len(matched)}")
    print(f"Downloaded:  {len(downloaded)}")
    print(f"Skipped:     {len(skipped)}")
    print(f"Failed:      {len(failed)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
