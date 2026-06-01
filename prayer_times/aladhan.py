"""Aladhan API client — location + date range in, structured prayer times out."""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

try:
    import certifi
except ImportError:
    certifi = None  # type: ignore[assignment]
from datetime import date, datetime
from typing import Any

from prayer_times.models import (
    PRAYER_NAMES,
    DaySchedule,
    Location,
    LocationByCity,
    LocationByCoords,
    PrayerTime,
    PrayerTimesResult,
)

BASE_URL = "https://api.aladhan.com/v1"

# Strip trailing timezone label, e.g. "05:12 (BST)" -> "05:12"
_TIME_RE = re.compile(r"^(\d{1,2}:\d{2})")


class AladhanError(Exception):
    """Raised when the Aladhan API returns an error or unexpected payload."""


def fetch_methods() -> list[dict[str, str | int]]:
    """Return available prayer calculation methods from Aladhan."""
    payload = _get_json("/methods", {})
    raw = payload["data"]
    entries = raw.items() if isinstance(raw, dict) else ((str(i), e) for i, e in enumerate(raw))
    return sorted(
        [
            {"id": int(entry["id"]), "name": entry.get("name", key)}
            for key, entry in entries
            if isinstance(entry, dict) and "id" in entry
        ],
        key=lambda m: m["id"],
    )


def fetch_prayer_times(
    location: Location,
    start: date,
    end: date,
    *,
    method: int = 2,
    school: int = 0,
) -> PrayerTimesResult:
    """Fetch prayer times for every day in [start, end] inclusive."""
    if start > end:
        raise ValueError(f"start date {start} must be on or before end date {end}")

    days: list[DaySchedule] = []
    for year, month in _months_in_range(start, end):
        month_days = _fetch_month(location, year, month, method=method, school=school)
        days.extend(d for d in month_days if start <= d.date <= end)

    return PrayerTimesResult(
        location=location,
        method=method,
        school=0 if school == 0 else 1,
        days=tuple(days),
    )


def _months_in_range(start: date, end: date) -> list[tuple[int, int]]:
    """Return (year, month) pairs covering the date range."""
    months: list[tuple[int, int]] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _fetch_month(
    location: Location,
    year: int,
    month: int,
    *,
    method: int,
    school: int,
) -> list[DaySchedule]:
    if isinstance(location, LocationByCity):
        path = f"/calendarByCity/{year}/{month}"
        params: dict[str, str | float] = {
            "city": location.city,
            "country": location.country,
        }
    else:
        path = f"/calendar/{year}/{month}"
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    params["method"] = method
    params["school"] = school

    payload = _get_json(path, params)
    return [_parse_day(entry) for entry in payload["data"]]


def _ssl_context() -> ssl.SSLContext | None:
    """Use certifi CA bundle when available (fixes macOS python.org SSL issues)."""
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def _get_json(path: str, params: dict[str, str | float]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=30, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise AladhanError(f"Network error calling Aladhan API: {exc}") from exc

    if payload.get("code") != 200:
        raise AladhanError(
            f"Aladhan API error: {payload.get('status', 'unknown')} — {payload.get('data')}"
        )
    return payload


def _parse_day(entry: dict[str, Any]) -> DaySchedule:
    timings = entry["timings"]
    meta = entry["meta"]
    timezone = meta["timezone"]

    gregorian = entry["date"]["gregorian"]["date"]  # DD-MM-YYYY
    day = datetime.strptime(gregorian, "%d-%m-%Y").date()

    prayers: list[PrayerTime] = []
    for name in PRAYER_NAMES:
        raw = timings[name]
        match = _TIME_RE.match(raw)
        if not match:
            raise AladhanError(f"Unexpected time format for {name}: {raw!r}")
        time_str = match.group(1)
        hour, minute = map(int, time_str.split(":"))
        prayers.append(
            PrayerTime(
                name=name,
                time=datetime(day.year, day.month, day.day, hour, minute),
            )
        )

    return DaySchedule(date=day, prayers=tuple(prayers), timezone=timezone)
