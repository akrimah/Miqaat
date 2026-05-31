# Prayer Times Calendar

Generate calendar events for the five daily prayers using the [Aladhan API](https://aladhan.com/prayer-times-api).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

(`certifi` fixes SSL certificate verification on macOS python.org installs.)

## Usage

By city:

```bash
python -m prayer_times --city London --country UK --from 2026-06-01 --to 2026-06-07
```

By coordinates (e.g. current GPS location):

```bash
python -m prayer_times --lat 51.5074 --lon -0.1278 --from 2026-06-01 --to 2026-06-07
```

Optional flags: `--method 2` (calculation method), `--school 0` (Asr: 0=Shafi, 1=Hanafi), `--json` (raw JSON output).
