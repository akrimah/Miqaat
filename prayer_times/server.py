"""FastAPI web server — serves marketing site, app UI, and prayer-times API."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from prayer_times.aladhan import AladhanError, fetch_methods, fetch_prayer_times
from prayer_times.ics import result_to_ics
from prayer_times.models import Location, LocationByCity, LocationByCoords
from prayer_times.serialize import result_to_dict

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
MARKETING_DIR = WEB_DIR / "marketing"
APP_DIR = WEB_DIR / "app"
MAX_RANGE_DAYS = 90

MARKETING_PAGES = {
    "how-it-works": "how-it-works.html",
    "faq": "faq.html",
    "about": "about.html",
    "contact": "contact.html",
    "privacy": "privacy.html",
    "terms": "terms.html",
}

app = FastAPI(title="Miqaat", version="0.3.0")


class LocationInput(BaseModel):
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def to_location(self) -> Location:
        has_city = self.city is not None or self.country is not None
        has_coords = self.latitude is not None or self.longitude is not None

        if has_city and has_coords:
            raise ValueError("Provide either city/country or latitude/longitude, not both")
        if has_city:
            if not self.city or not self.country:
                raise ValueError("Both city and country are required")
            return LocationByCity(city=self.city.strip(), country=self.country.strip())
        if has_coords:
            if self.latitude is None or self.longitude is None:
                raise ValueError("Both latitude and longitude are required")
            return LocationByCoords(latitude=self.latitude, longitude=self.longitude)
        raise ValueError("Location is required")


class PrayerTimesRequest(BaseModel):
    location: LocationInput
    start: date
    end: date
    method: int = Field(default=2, ge=1, le=99)
    school: Literal[0, 1] = 0

    @model_validator(mode="after")
    def validate_date_range(self) -> PrayerTimesRequest:
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        if (self.end - self.start).days + 1 > MAX_RANGE_DAYS:
            raise ValueError(f"Date range cannot exceed {MAX_RANGE_DAYS} days")
        return self


def _fetch(request: PrayerTimesRequest):
    try:
        location = request.location.to_location()
        return fetch_prayer_times(
            location,
            request.start,
            request.end,
            method=request.method,
            school=request.school,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AladhanError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@lru_cache
def _cached_methods() -> tuple[dict[str, str | int], ...]:
    try:
        return tuple(fetch_methods())
    except AladhanError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/")
def home() -> FileResponse:
    return FileResponse(MARKETING_DIR / "index.html")


@app.get("/app")
def app_page() -> FileResponse:
    return FileResponse(APP_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/methods")
def get_methods() -> list[dict[str, str | int]]:
    return list(_cached_methods())


@app.post("/api/prayer-times")
def post_prayer_times(request: PrayerTimesRequest) -> dict:
    result = _fetch(request)
    return result_to_dict(result)


@app.post("/api/export/ics")
def post_export_ics(request: PrayerTimesRequest) -> Response:
    result = _fetch(request)
    ics_bytes = result_to_ics(result)
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="prayer-times.ics"'},
    )


@app.get("/robots.txt")
def robots() -> FileResponse:
    return FileResponse(MARKETING_DIR / "static" / "robots.txt", media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap() -> FileResponse:
    return FileResponse(MARKETING_DIR / "static" / "sitemap.xml", media_type="application/xml")


@app.get("/{page_name}")
def marketing_page(page_name: str) -> FileResponse:
    filename = MARKETING_PAGES.get(page_name)
    if filename is None:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(MARKETING_DIR / filename)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    if exc.status_code != 404:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    if request.url.path.startswith("/api"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    page = MARKETING_DIR / "404.html"
    return HTMLResponse(page.read_text(encoding="utf-8"), status_code=404)


app.mount("/static", StaticFiles(directory=MARKETING_DIR / "static"), name="marketing_static")
app.mount("/app/static", StaticFiles(directory=APP_DIR / "static"), name="app_static")
