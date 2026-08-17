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


LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"]


def antardashas(maha_lord: str, start: datetime, maha_years: float) -> list[dict]:
    """Sub-periods of any period, one level down.

    The rule is the same at every depth: the nine lords run in Vimshottari
    order beginning with the parent's own lord, and each takes the share of
    the parent that its 120-year allocation represents. So this same
    function produces antardashas from a mahadasha, pratyantardashas from
    an antardasha, and so on -- see `subdivide`.

    `maha_years` is passed rather than looked up because the first
    mahadasha is shortened by the balance at birth, and everything nested
    inside it has to shrink to match.
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


def subdivide(period: dict) -> list[dict]:
    """One level below the given period, whatever depth it sits at.

    The span is measured from the stored timestamps rather than the
    `years` field, because that field is rounded for display. Feeding the
    rounded value back in compounds at every level -- by Sookshma it was
    enough to push a period past the end of its own parent.
    """
    start = datetime.fromisoformat(period["start"])
    end = datetime.fromisoformat(period["end"])
    exact_years = (end - start).total_seconds() / (DAYS_PER_YEAR * 86400.0)
    return antardashas(period["lord"], start, exact_years)


def dasha_chain(timeline: list[dict], as_of: datetime, depth: int = 4) -> list[dict]:
    """The nested periods running at `as_of`, from mahadasha downwards.

    Returns one entry per level with its siblings alongside, so a caller
    can show the running Pratyantardasha in the context of the ones either
    side of it rather than on its own.
    """
    chain = []
    candidates = timeline

    for level in range(depth):
        running = next(
            (p for p in candidates
             if datetime.fromisoformat(p["start"]) <= as_of <= datetime.fromisoformat(p["end"])),
            None,
        )
        if running is None:
            break
        index = candidates.index(running)
        chain.append({
            "level": LEVEL_NAMES[level],
            "period": running,
            "siblings": candidates,
            "index": index,
        })
        candidates = subdivide(running)

    return chain


def window(periods: list[dict], index: int, before: int = 5, after: int = 9) -> list[dict]:
    """A slice around a period, clamped to the ends of the list.

    Printed horoscopes present sub-periods as a band around the current
    one rather than the whole set, which is what `before`/`after` describe.
    """
    lo = max(0, index - before)
    hi = min(len(periods), index + after + 1)
    return periods[lo:hi]


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
    subs = subdivide(maha)
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
        following = subdivide(timeline[maha_index + 1])[0]
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
