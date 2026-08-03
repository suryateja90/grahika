"""Vimshottari Mahadasha (planetary period) timeline.

Standard 120-year cycle, 9 lords, fixed durations. The lord of the
nakshatra the Moon occupies at birth starts the sequence; the portion of
that nakshatra already elapsed at birth reduces its first period
proportionally (the "balance of dasha" at birth).

Only mahadasha (level-1) periods are computed here. Antardasha
(sub-periods) are a natural next step once mahadasha output is verified
against pundit-checked charts.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.astro.ephemeris import NAKSHATRA_SPAN

DAYS_PER_YEAR = 365.2425

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

assert sum(DASHA_YEARS.values()) == 120


def vimshottari_timeline(moon_longitude: float, birth_dt: datetime, cycles: int = 1) -> list[dict]:
    """Mahadasha periods from birth through `cycles` full 120-year cycles."""
    moon_longitude = moon_longitude % 360.0
    nakshatra_idx = int(moon_longitude // NAKSHATRA_SPAN)
    lord_start_idx = nakshatra_idx % 9

    elapsed_fraction = (moon_longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_lord = DASHA_ORDER[lord_start_idx]
    first_period_years = DASHA_YEARS[first_lord] * (1 - elapsed_fraction)

    periods = []
    cursor = birth_dt
    total_periods = 9 * cycles

    for i in range(total_periods):
        lord = DASHA_ORDER[(lord_start_idx + i) % 9]
        years = first_period_years if i == 0 else DASHA_YEARS[lord]
        duration = timedelta(days=years * DAYS_PER_YEAR)
        start = cursor
        end = cursor + duration
        periods.append({
            "lord": lord,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "years": round(years, 4),
        })
        cursor = end

    return periods
