"""Command-line entry point for fetching prayer times."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from prayer_times.aladhan import AladhanError, fetch_prayer_times
from prayer_times.models import LocationByCity, LocationByCoords
from prayer_times.serialize import result_to_json


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}; use YYYY-MM-DD"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Islamic prayer times from the Aladhan API.",
    )
    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument("--city", help="City name (requires --country)")
    location.add_argument("--lat", type=float, dest="latitude", help="Latitude")
    parser.add_argument("--country", help="Country name or code (with --city)")
    parser.add_argument("--lon", type=float, dest="longitude", help="Longitude (with --lat)")

    parser.add_argument("--from", dest="start", type=_parse_date, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="end", type=_parse_date, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--method",
        type=int,
        default=2,
        help="Calculation method ID (default: 2 = ISNA)",
    )
    parser.add_argument(
        "--school",
        type=int,
        choices=[0, 1],
        default=0,
        help="Asr juristic school: 0=Shafi, 1=Hanafi (default: 0)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a table")
    return parser


def _resolve_location(args: argparse.Namespace):
    if args.city:
        if not args.country:
            raise SystemExit("Error: --country is required when using --city")
        return LocationByCity(city=args.city, country=args.country)
    if args.latitude is None or args.longitude is None:
        raise SystemExit("Error: both --lat and --lon are required together")
    return LocationByCoords(latitude=args.latitude, longitude=args.longitude)


def _format_table(result) -> str:
    lines: list[str] = []
    for day in result.days:
        lines.append(f"\n{day.date.isoformat()} ({day.timezone})")
        for prayer in day.prayers:
            lines.append(f"  {prayer.name:<8} {prayer.time.strftime('%H:%M')}")
    return "\n".join(lines).lstrip()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        location = _resolve_location(args)
        result = fetch_prayer_times(
            location,
            args.start,
            args.end,
            method=args.method,
            school=args.school,
        )
    except (AladhanError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output = result_to_json(result) if args.json else _format_table(result)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
