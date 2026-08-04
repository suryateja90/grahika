"""Kaal Sarp Yoga and Sade Sati.

Kaal Sarp Yoga is a simple, well-defined geometric check on the birth
chart alone: presence is determined once, at birth, forever.

Sade Sati is fundamentally different -- it depends on where *transiting*
Saturn is *right now* (or at any given "as of" date) relative to the
natal Moon, not just the birth chart. That means it needs a transit
search rather than a single ephemeris call. The search here steps
through time in coarse increments and merges nearby true/false runs to
approximate the traditional handling of Saturn's retrograde wobble at a
window's boundary (it can dip in and out of the 12th/1st/2nd signs
before settling) -- it is not an exact reproduction of any specific
classical method, and duration/phase-boundary conventions vary by
tradition. Treat this the same as everything else in tests/fixtures/:
verify against a pundit or reference site before trusting it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.astro import ephemeris

PRIME_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

SATURN_TRANSIT_STEP_DAYS = 15
MERGE_GAP_DAYS = 400
LOOKBACK_YEARS = 5
LOOKAHEAD_YEARS = 32  # > one full Saturn orbit (~29.5 years), guarantees finding the next window


def kaal_sarp_yoga(bodies: dict) -> dict:
    """All 7 classical planets fall within the arc from Rahu to Ketu, on one side."""
    rahu = bodies["Rahu"]["longitude"]
    ketu_span = 180.0  # Ketu is always exactly opposite Rahu

    def arc_span(lon: float) -> float:
        return (lon - rahu) % 360.0

    spans = [arc_span(bodies[p]["longitude"]) for p in PRIME_PLANETS]

    all_before_ketu = all(0.0 <= s <= ketu_span for s in spans)
    all_after_ketu = all(ketu_span <= s <= 360.0 for s in spans)

    present = all_before_ketu or all_after_ketu
    direction = "Rahu to Ketu" if all_before_ketu else ("Ketu to Rahu" if all_after_ketu else None)

    return {"present": present, "direction": direction}


def _in_window(saturn_sign_index: int, moon_sign_index: int) -> bool:
    return saturn_sign_index in {
        (moon_sign_index - 1) % 12,
        moon_sign_index,
        (moon_sign_index + 1) % 12,
    }


def _phase(saturn_sign_index: int, moon_sign_index: int) -> str:
    if saturn_sign_index == (moon_sign_index - 1) % 12:
        return "rising"
    if saturn_sign_index == moon_sign_index:
        return "peak"
    return "setting"


def sade_sati_status(moon_sign_index: int, ayanamsa: str = "lahiri", as_of: datetime | None = None) -> dict:
    as_of = as_of or datetime.now(timezone.utc)

    search_start = as_of - timedelta(days=365 * LOOKBACK_YEARS)
    search_end = as_of + timedelta(days=365 * LOOKAHEAD_YEARS)

    samples = []
    t = search_start
    while t <= search_end:
        sign = ephemeris.saturn_sign_index(t, ayanamsa)
        samples.append((t, _in_window(sign, moon_sign_index)))
        t += timedelta(days=SATURN_TRANSIT_STEP_DAYS)

    raw_runs = []
    run_start = None
    for t, inside in samples:
        if inside and run_start is None:
            run_start = t
        elif not inside and run_start is not None:
            raw_runs.append((run_start, t))
            run_start = None
    if run_start is not None:
        raw_runs.append((run_start, samples[-1][0]))

    merged = []
    for start, end in raw_runs:
        if merged and (start - merged[-1][1]).days <= MERGE_GAP_DAYS:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append([start, end])

    current = next((ep for ep in merged if ep[0] <= as_of <= ep[1]), None)
    upcoming = next((ep for ep in merged if ep[0] > as_of), None)

    phase = None
    if current:
        phase = _phase(ephemeris.saturn_sign_index(as_of, ayanamsa), moon_sign_index)

    return {
        "in_sade_sati": current is not None,
        "phase": phase,
        "current_window_start": current[0].date().isoformat() if current else None,
        "current_window_end": current[1].date().isoformat() if current else None,
        "next_window_start": upcoming[0].date().isoformat() if upcoming else None,
    }
