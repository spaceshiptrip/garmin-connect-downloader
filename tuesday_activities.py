from datetime import datetime, date
from pathlib import Path
import getpass
import json
import re

from garminconnect import Garmin

START_DATE = date(2025, 10, 1)
OUTPUT_DIR = Path("tuesday_gpx")


def init_client():
    tokenstore = Path("~/.garminconnect").expanduser()

    # First try saved tokens
    try:
        client = Garmin()
        client.login(str(tokenstore))
        print("Logged in using saved token.")
        return client
    except Exception:
        pass

    # Fall back to interactive login
    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")
    client = Garmin(email=email, password=password, return_on_mfa=True)

    result1, result2 = client.login()
    if result1 == "needs_mfa":
        mfa_code = input("Please enter your MFA code: ")
        client.resume_login(result2, mfa_code)

    client.garth.dump(str(tokenstore))
    print("Logged in and saved new token.")
    return client


def parse_activity_date(activity):
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
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except Exception:
            pass
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            pass
    return None


def safe_name(text):
    text = text or "activity"
    text = re.sub(r"[^\w\-\.]+", "_", text.strip())
    return text[:120]


def main():
    client = init_client()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    limit = 100
    start = 0
    tuesday_activities = []

    while True:
        batch = client.get_activities(start, limit)
        if not batch:
            break

        stop_early = False

        for act in batch:
            act_date = parse_activity_date(act)
            if act_date is None:
                continue

            if act_date < START_DATE:
                stop_early = True
                break

            if act_date.weekday() == 1:  # Tuesday
                tuesday_activities.append(act)

        if stop_early or len(batch) < limit:
            break

        start += limit

    print(f"Found {len(tuesday_activities)} Tuesday activities since {START_DATE.isoformat()}")

    downloaded = []
    skipped = []
    failed = []

    for act in tuesday_activities:
        activity_id = act.get("activityId")
        act_date = parse_activity_date(act)
        activity_name = act.get("activityName", "Unnamed Activity")
        filename = OUTPUT_DIR / f"{act_date}_{safe_name(activity_name)}_{activity_id}.gpx"

        if filename.exists():
            print(f"Skipping existing: {filename.name}")
            skipped.append(str(filename))
            continue

        try:
            gpx_data = client.download_activity(
                activity_id,
                dl_fmt=client.ActivityDownloadFormat.GPX,
            )
            with open(filename, "wb") as f:
                f.write(gpx_data)

            print(f"Saved: {filename}")
            downloaded.append(
                {
                    "activityId": activity_id,
                    "date": str(act_date),
                    "name": activity_name,
                    "file": str(filename),
                }
            )
        except Exception as e:
            print(f"Failed GPX download for activity {activity_id} ({activity_name}): {e}")
            failed.append(
                {
                    "activityId": activity_id,
                    "date": str(act_date) if act_date else None,
                    "name": activity_name,
                    "error": str(e),
                }
            )

    manifest = {
        "start_date": START_DATE.isoformat(),
        "output_dir": str(OUTPUT_DIR),
        "downloaded_count": len(downloaded),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
    }

    with open("tuesday_gpx_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print()
    print(f"Downloaded: {len(downloaded)}")
    print(f"Skipped existing: {len(skipped)}")
    print(f"Failed: {len(failed)}")
    print("Manifest saved to tuesday_gpx_manifest.json")


if __name__ == "__main__":
    main()
