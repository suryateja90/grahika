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


# This route is the fallback now: the browser asks Nominatim directly, so
# each visitor spends their own rate limit instead of pooling into this
# server's single outbound address. That pooling is what broke place search
# in production -- on a shared host the address is already spent by other
# tenants, and Nominatim answered 429 to a query that succeeded from a
# laptop against identical code.
#
# Caching matters more here than it used to. Requests reaching this path are
# the ones a browser could not make, so they are rarer and more costly to
# lose; serving a repeat from memory keeps the one shared address further
# from the limit. The cache lives for the process, which on a host that
# sleeps when idle is a few hours at most.
_CACHE_LIMIT = 512
_cache: dict[str, list[dict]] = {}


def search_places(query: str, limit: int = 5) -> list[dict]:
    key = f"{query.strip().lower()}|{limit}"
    if key in _cache:
        return _cache[key]

    params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": limit})
    req = urllib.request.Request(f"{NOMINATIM_SEARCH_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=8) as resp:
        results = json.loads(resp.read().decode())

    places = [
        {
            "display_name": r["display_name"],
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"]),
        }
        for r in results
    ]

    # Plain FIFO eviction rather than a true LRU: the working set is one
    # session's searches, and the oldest inserted key is old enough.
    if len(_cache) >= _CACHE_LIMIT:
        del _cache[next(iter(_cache))]
    _cache[key] = places
    return places


def timezone_name_for(lat: float, lon: float) -> str:
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(f"Could not resolve a timezone for coordinates ({lat}, {lon})")
    return tz_name


def localize(naive_dt: datetime, lat: float, lon: float) -> datetime:
    """Attach the correct historical UTC offset for this place and date."""
    tz = pytz.timezone(timezone_name_for(lat, lon))
    return tz.localize(naive_dt)


def ensure_aware(dt: datetime, lat: float, lon: float) -> datetime:
    """Pass through an already-aware datetime; localize a naive one."""
    return dt if dt.tzinfo is not None else localize(dt, lat, lon)
