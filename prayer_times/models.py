from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

# The five obligatory daily prayers (Sunrise is intentionally excluded).
PRAYER_NAMES = ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")


@dataclass(frozen=True)
class LocationByCity:
    city: str
    country: str


@dataclass(frozen=True)
class LocationByCoords:
    latitude: float
    longitude: float


Location = LocationByCity | LocationByCoords


@dataclass(frozen=True)
class PrayerTime:
    name: str
    time: datetime


@dataclass(frozen=True)
class DaySchedule:
    date: date
    prayers: tuple[PrayerTime, ...]
    timezone: str


@dataclass(frozen=True)
class PrayerTimesResult:
    location: Location
    method: int
    school: Literal[0, 1]
    days: tuple[DaySchedule, ...]
