# Miqaat

Prayer times for home, work, and travel. Built with Python (FastAPI) and a vanilla HTML/CSS/JS frontend.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn prayer_times.server:app --reload
```

- **Website:** http://127.0.0.1:8000
- **Prayer app:** http://127.0.0.1:8000/app

## Project structure

```
prayer_times/     # Core API + business logic (protected for mobile reuse)
web/
  marketing/      # Public website (home, FAQ, about, legal pages)
  app/            # Prayer times tool UI
docs/API.md       # API contract for future Flutter apps
mobile/           # Placeholder for future iOS/Android apps
```

## CLI

```bash
python3 -m prayer_times --city London --country UK --from 2026-06-01 --to 2026-06-07
```

## Deploy (Render)

Connect the GitHub repo to [Render](https://render.com). See [`render.yaml`](render.yaml).

Build: `pip install -r requirements.txt`  
Start: `uvicorn prayer_times.server:app --host 0.0.0.0 --port $PORT`
