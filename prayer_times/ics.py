"""Convert prayer times to iCalendar (.ics) format."""

from __future__ import annotations

from datetime import timedelta

from icalendar import Calendar, Event

from prayer_times.models import Location, LocationByCity, LocationByCoords, PrayerTimesResult

EVENT_DURATION = timedelta(minutes=15)


def _location_label(location: Location) -> str:
    if isinstance(location, LocationByCity):
        return f"{location.city}, {location.country}"
    return f"{location.latitude:.4f}, {location.longitude:.4f}"


def result_to_ics(result: PrayerTimesResult) -> bytes:
    """Build an .ics calendar with one event per prayer per day."""
    label = _location_label(result.location)
    cal = Calendar()
    cal.add("prodid", "-//Prayer Times//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", f"Prayer Times — {label}")

    for day in result.days:
        for prayer in day.prayers:
            event = Event()
            event.add("summary", f"{prayer.name} — {label}")
            event.add("dtstart", prayer.time)
            event.add("dtend", prayer.time + EVENT_DURATION)
            event.add("uid", f"{day.date.isoformat()}-{prayer.name}@prayer-times")
            cal.add_component(event)

    return cal.to_ical()
