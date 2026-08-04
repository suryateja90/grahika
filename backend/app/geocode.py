"""Place-name lookup and historical timezone resolution.

Both free, no API keys:
- Nominatim (OpenStreetMap) for place name -> lat/lon. Usage policy caps
  this at ~1 request/second and asks for an identifying User-Agent -- fine
  here since lookups are user-initiated (one search per button click), not
  autocomplete-as-you-type.
- timezonefinder + pytz for lat/lon (+ a date) -> the correct historical
  UTC offset for that place, entirely offline. This is what actually fixes
  the classic "wrong chart from a naive fixed UTC offset" problem -- e.g.
  India's tz database captures the pre-1906 local mean time offset, not
  just today's fixed +05:30.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime

import pytz
from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GrahikaApp/0.1 (contact: suryafacts@gmail.com)"


def search_places(query: str, limit: int = 5) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": limit})
    req = urllib.request.Request(f"{NOMINATIM_SEARCH_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=8) as resp:
        results = json.loads(resp.read().decode())
    return [
        {
            "display_name": r["display_name"],
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"]),
        }
        for r in results
    ]


def timezone_name_for(lat: float, lon: float) -> str:
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(f"Could not resolve a timezone for coordinates ({lat}, {lon})")
    return tz_name


def localize(naive_dt: datetime, lat: float, lon: float) -> datetime:
    """Attach the correct historical UTC offset for this place and date."""
    tz = pytz.timezone(timezone_name_for(lat, lon))
    return tz.localize(naive_dt)
