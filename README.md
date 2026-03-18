# Garmin Connect Downloader

A simple CLI tool to download Garmin activities with flexible filters:

- Date range
- Interval (e.g. all Tuesdays, weekdays, every other day)
- Sport type (running, hiking, cycling, etc.)
- Download format (GPX, FIT, TCX, etc.)

---

## 🚀 Features

- Supports Garmin login with MFA (TFA)
- Reuses saved auth tokens (no repeated logins)
- Filter by date range and interval
- Filter by sport/activity type
- Download multiple formats (GPX, FIT, TCX, etc.)
- Outputs:
  - JSON manifest
  - CSV summary
- Skips already-downloaded files

---

## 📦 Installation

    python3 -m venv .venv
    source .venv/bin/activate

    pip install --upgrade pip
    pip install garminconnect

---

## 🔐 First Run (Authentication)

On first run:

- Enter Garmin email
- Enter password
- Enter MFA code (if enabled)

Tokens are saved locally in:

    ~/.garminconnect

Future runs will reuse the token and skip login.

---

## 🧑‍💻 Usage

Basic example:

    python3 garmin_activity_downloader.py \
      --start-date 2025-10-01 \
      --end-date 2026-03-18 \
      --interval all_tuesdays \
      --sport any \
      --download-format gpx \
      --output-dir tuesday_gpx

---

## ⚙️ Command Line Options

| Option | Description |
|--------|-------------|
| --start-date | Start date (YYYY-MM-DD) |
| --end-date | End date (default: today) |
| --interval | Filter interval (e.g. all_tuesdays, every_day) |
| --sport | Activity type filter |
| --download-format | gpx, fit, tcx, original, csv |
| --output-dir | Output directory |
| --list-only | Preview results without downloading |
| --overwrite | Re-download existing files |
| --summary-csv | Output CSV file |
| --manifest | Output JSON manifest |

---

## 📅 Interval Examples

| Interval | Description |
|----------|-------------|
| all_tuesdays | Every Tuesday |
| every_day | All days |
| every_other_day | Every 2 days |
| every_3_days | Every 3 days |
| weekdays | Monday–Friday |
| weekends | Saturday–Sunday |

---

## 🏃 Sport Filters

Examples:

- running
- trail_running
- hiking
- cycling
- any (default)

---

## 📁 Output

### GPX / FIT / TCX Files

Saved to your output directory:

    tuesday_gpx/
      2025-10-07_Morning_Run_running_123456789.gpx

---

### CSV Summary

    download_summary.csv

Contains:

- date
- activity name
- distance
- duration
- elevation gain

---

### JSON Manifest

    download_manifest.json

Tracks:

- downloaded files
- skipped files
- failed downloads

---

## 🔍 Preview Only

    python3 garmin_activity_downloader.py \
      --start-date 2025-10-01 \
      --interval all_tuesdays \
      --list-only

---

## ⚠️ Notes

- Not all activities support GPX export (e.g. strength training)
- Garmin authentication may occasionally fail due to API changes
- Tokens may expire → delete ~/.garminconnect to reset

---

## 🧠 Example Use Case

Download all Tuesday runs since October 2025:

    python3 garmin_activity_downloader.py \
      --start-date 2025-10-01 \
      --interval all_tuesdays \
      --sport running \
      --download-format gpx \
      --output-dir tuesday_runs

---

## 📜 License

MIT
