"""Shared JSON serialization for CLI and web API."""

from __future__ import annotations

import json

from prayer_times.models import PrayerTimesResult


def result_to_dict(result: PrayerTimesResult) -> dict:
    return {
        "location": result.location.__dict__,
        "method": result.method,
        "school": result.school,
        "days": [
            {
                "date": day.date.isoformat(),
                "timezone": day.timezone,
                "prayers": [
                    {"name": p.name, "time": p.time.strftime("%H:%M")}
                    for p in day.prayers
                ],
            }
            for day in result.days
        ],
    }


def result_to_json(result: PrayerTimesResult, *, indent: int | None = 2) -> str:
    return json.dumps(result_to_dict(result), indent=indent)
