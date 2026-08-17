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


def antardashas(maha_lord: str, start: datetime, maha_years: float) -> list[dict]:
    """Sub-periods within one mahadasha.

    The nine lords run in the same order, beginning with the mahadasha lord
    itself, and each takes the share of the parent period that its own
    120-year allocation represents.

    `maha_years` is passed rather than looked up because the first
    mahadasha is shortened by the balance at birth, and its antardashas
    have to shrink with it.
    """
    lord_index = DASHA_ORDER.index(maha_lord)
    periods = []
    cursor = start

    for i in range(9):
        lord = DASHA_ORDER[(lord_index + i) % 9]
        years = maha_years * DASHA_YEARS[lord] / 120.0
        end = cursor + timedelta(days=years * DAYS_PER_YEAR)
        periods.append({
            "lord": lord,
            "start": cursor.isoformat(),
            "end": end.isoformat(),
            "years": round(years, 4),
        })
        cursor = end

    return periods


def current_periods(timeline: list[dict], as_of: datetime) -> dict:
    """Which mahadasha and antardasha are running at `as_of`, plus the one
    that follows. Returns nulls rather than raising when the moment falls
    outside the computed span."""
    position = next(
        ((i, p) for i, p in enumerate(timeline)
         if datetime.fromisoformat(p["start"]) <= as_of <= datetime.fromisoformat(p["end"])),
        None,
    )
    if position is None:
        return {"mahadasha": None, "antardasha": None, "next_antardasha": None}

    maha_index, maha = position
    subs = antardashas(maha["lord"], datetime.fromisoformat(maha["start"]), maha["years"])
    index = next(
        (i for i, p in enumerate(subs)
         if datetime.fromisoformat(p["start"]) <= as_of <= datetime.fromisoformat(p["end"])),
        None,
    )
    if index is None:
        return {"mahadasha": maha, "antardasha": None, "next_antardasha": None}

    # On the last antardasha of a mahadasha the next one belongs to the
    # following mahadasha. Returning null there would leave the report's
    # "next period" blank for years at a time.
    if index + 1 < len(subs):
        following = subs[index + 1]
    elif maha_index + 1 < len(timeline):
        next_maha = timeline[maha_index + 1]
        following = antardashas(
            next_maha["lord"], datetime.fromisoformat(next_maha["start"]), next_maha["years"]
        )[0]
    else:
        following = None

    return {
        "mahadasha": maha,
        "antardasha": subs[index],
        "next_antardasha": following,
        "antardashas": subs,
    }


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
