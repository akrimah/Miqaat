# Prayer Times Calendar

Generate calendar events for the five daily prayers using the [Aladhan API](https://aladhan.com/prayer-times-api).

Includes a **web UI** (FastAPI + vanilla HTML/CSS/JS) and a **CLI** for scripting.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

(`certifi` fixes SSL certificate verification on macOS python.org installs.)

## Web app (local)

```bash
uvicorn prayer_times.server:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

Features:

- City or GPS location
- Date range (up to 90 days)
- Calculation method and Asr school settings
- Prayer times display with a highlighted “Today” card
- Download `.ics` for Google Calendar, Apple Calendar, etc.

## CLI

By city:

```bash
python3 -m prayer_times --city London --country UK --from 2026-06-01 --to 2026-06-07
```

By coordinates:

```bash
python3 -m prayer_times --lat 51.5074 --lon -0.1278 --from 2026-06-01 --to 2026-06-07
```

Optional flags: `--method 2`, `--school 0`, `--json`.

## Project structure

```
prayer_times/
  aladhan.py    # Aladhan API client
  models.py     # Data types
  serialize.py  # JSON output (shared by CLI + API)
  ics.py        # .ics calendar export
  server.py     # FastAPI web server
  cli.py        # Command-line interface
web/
  index.html
  static/style.css
  static/app.js
```

