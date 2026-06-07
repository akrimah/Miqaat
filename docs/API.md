# Miqaat API

REST API for prayer times. Used by the web app (`/app`) and future Flutter mobile apps.

Base URL: same origin as the website (e.g. `https://miqaat.onrender.com`).

## Endpoints

### `GET /api/health`

Health check for monitoring.

```json
{ "status": "ok" }
```

### `GET /api/methods`

List available prayer calculation methods.

```json
[
  { "id": 2, "name": "Islamic Society of North America (ISNA)" }
]
```

### `POST /api/prayer-times`

Fetch prayer times for a date range.

**Request body:**

```json
{
  "location": { "city": "London", "country": "UK" },
  "start": "2026-06-01",
  "end": "2026-06-30",
  "method": 2,
  "school": 0
}
```

Or by coordinates:

```json
{
  "location": { "latitude": 51.5074, "longitude": -0.1278 },
  "start": "2026-06-01",
  "end": "2026-06-07",
  "method": 2,
  "school": 0
}
```

- `school`: `0` = Shafi, `1` = Hanafi
- Max range: 90 days

### `POST /api/export/ics`

Same request body as `/api/prayer-times`. Returns a `.ics` calendar file.

## Errors

- `400` — invalid input (bad dates, missing location)
- `502` — Aladhan API unavailable
