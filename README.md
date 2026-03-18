# Garmin Connect Downloader

A simple CLI tool to download Garmin activities with flexible filters:

- Date range
- Interval (e.g. all Tuesdays, weekdays, every other day)
- Sport type (running, hiking, cycling, etc.)
- **Activity name patterns (wildcards, case-insensitive)**
- Download format (GPX, FIT, TCX, etc.)

---

## 🚀 Features

- Supports Garmin login with MFA (TFA)
- Reuses saved auth tokens (no repeated logins)
- Filter by date range and interval
- Filter by sport/activity type
- **Filter by activity name using wildcards (`*pattern*`)**
- Case-insensitive matching
- Download multiple formats (GPX, FIT, TCX, etc.)
- Outputs:
  - JSON manifest
  - CSV summary
- Skips already-downloaded files

---

## 📦 Installation

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install garminconnect
````

---

## 🔐 First Run (Authentication)

On first run:

* Enter Garmin email
* Enter password
* Enter MFA code (if enabled)

Tokens are saved locally in:

```
~/.garminconnect
```

Future runs will reuse the token and skip login.

---

## 🧑‍💻 Usage

Basic example:

```bash
python3 garmin_activity_downloader.py \
  --start-date 2025-10-01 \
  --end-date 2026-03-18 \
  --interval all_tuesdays \
  --sport any \
  --download-format gpx \
  --output-dir tuesday_gpx
```

---

## 🔎 Name Pattern Filtering (NEW)

You can filter activities by name using wildcard patterns:

* `*` = wildcard
* Case-insensitive

### Examples

#### Match anything containing "La Verne"

```bash
--name-pattern "*la*verne*"
```

Matches:

* `La Verne Trail Run`
* `LA VERNE HIKE`
* `Morning run - La Verne`

---

#### Match activities starting with "Home"

```bash
--name-pattern "Home*"
```

Matches:

* `Home Run`
* `Home to Trail`

---

#### Exclude patterns

```bash
--name-pattern "*la*verne*" \
--exclude-name-pattern "*test*"
```

---

#### Real Example

```bash
python3 garmin_activity_downloader.py \
  --start-date 2025-01-01 \
  --name-pattern "*la*verne*" \
  --download-format gpx \
  --output-dir laverne_gpx
```

---

## ⚙️ Command Line Options

| Option                 | Description                                    |
| ---------------------- | ---------------------------------------------- |
| --start-date           | Start date (YYYY-MM-DD)                        |
| --end-date             | End date (default: today)                      |
| --interval             | Filter interval (e.g. all_tuesdays, every_day) |
| --sport                | Activity type filter                           |
| --name-pattern         | Include activity names (supports `*` wildcard) |
| --exclude-name-pattern | Exclude activity names                         |
| --download-format      | gpx, fit, tcx, original, csv                   |
| --output-dir           | Output directory                               |
| --list-only            | Preview results without downloading            |
| --overwrite            | Re-download existing files                     |
| --summary-csv          | Output CSV file                                |
| --manifest             | Output JSON manifest                           |

---

## 📅 Interval Examples

| Interval        | Description     |
| --------------- | --------------- |
| all_tuesdays    | Every Tuesday   |
| monday          | All Mondays     |
| wednesday       | All Wednesdays  |
| every_day       | All days        |
| every_other_day | Every 2 days    |
| every_3_days    | Every 3 days    |
| weekdays        | Monday–Friday   |
| weekends        | Saturday–Sunday |

---

## 🏃 Sport Filters

Examples:

* running
* trail_running
* hiking
* cycling
* any (default)

> Note: Some activities (e.g. pickleball) may not be categorized by Garmin and may require `--sport any` + `--name-pattern`.

---

## 📁 Output

### GPX / FIT / TCX Files

Saved to your output directory:

```
tuesday_gpx/
  2025-10-07_Morning_Run_running_123456789.gpx
```

---

### CSV Summary

```
download_summary.csv
```

Contains:

* date
* activity name
* distance
* duration
* elevation gain

---

### JSON Manifest

```
download_manifest.json
```

Tracks:

* downloaded files
* skipped files
* failed downloads

---

## 🔍 Preview Only

```bash
python3 garmin_activity_downloader.py \
  --start-date 2025-10-01 \
  --interval all_tuesdays \
  --list-only
```

---

## ⚠️ Notes

* Not all activities support GPX export (e.g. strength training)
* Garmin authentication may occasionally fail due to API changes
* Tokens may expire → delete `~/.garminconnect` to reset
* Planned routes/courses are **not currently supported** (activities only)

---

## 🧠 Example Use Cases

### Download all Tuesday runs since October 2025

```bash
python3 garmin_activity_downloader.py \
  --start-date 2025-10-01 \
  --interval all_tuesdays \
  --sport running \
  --download-format gpx \
  --output-dir tuesday_runs
```

---

### Download all activities containing "La Verne"

```bash
python3 garmin_activity_downloader.py \
  --start-date 2025-01-01 \
  --sport any \
  --name-pattern "*la*verne*" \
  --download-format gpx \
  --output-dir laverne_gpx
```

---

### Download all "Home" activities ever

```bash
python3 garmin_activity_downloader.py \
  --start-date 2000-01-01 \
  --name-pattern "home*" \
  --download-format gpx \
  --output-dir home_gpx
```

---

## 📜 License

MIT

