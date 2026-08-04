"""Sidereal planetary positions via Swiss Ephemeris (pyswisseph).

Uses the built-in Moshier analytical model (SEFLG_MOSEPH) rather than the
JPL/Swiss Ephemeris data files (SEFLG_SWIEPH). Moshier needs no downloaded
.se1 files, is accurate to ~1 arcsecond for centuries around the present,
and is more than sufficient for horoscope-grade astrology. If a future
edge case demands file-based precision, swap the flag and ship the data
files -- the call sites here don't need to change.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import swisseph as swe

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

AYANAMSA_MODES = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "kp": swe.SIDM_KRISHNAMURTI,
    "true_chitra": swe.SIDM_TRUE_CITRA,
}

_PLANET_CODES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

NAKSHATRA_SPAN = 360.0 / 27.0
SIGN_SPAN = 30.0


def sign_index(longitude: float) -> int:
    return int(longitude % 360.0 // SIGN_SPAN)


def nakshatra_index(longitude: float) -> int:
    return int(longitude % 360.0 // NAKSHATRA_SPAN)


def julian_day_utc(dt_utc: datetime) -> float:
    if dt_utc.tzinfo is None:
        raise ValueError("dt_utc must be timezone-aware")
    dt_utc = dt_utc.astimezone(timezone.utc)
    hour = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def _planet_position(jd: float, code: int, flags: int) -> tuple[float, bool]:
    result, _ = swe.calc_ut(jd, code, flags)
    longitude = result[0]
    speed = result[3]
    return longitude, speed < 0


def compute_positions(
    dt_utc: datetime,
    lat: float,
    lon: float,
    ayanamsa: str = "lahiri",
    node_type: Literal["mean", "true"] = "mean",
) -> dict:
    """Sidereal longitudes for the 7 classical planets, Rahu/Ketu, and the Ascendant.

    Returns degrees 0-360 (tropical zero point at Aries 0 in the chosen
    ayanamsa's sidereal frame), plus derived sign/nakshatra placement.
    """
    if ayanamsa not in AYANAMSA_MODES:
        raise ValueError(f"Unknown ayanamsa '{ayanamsa}'. Choose from: {list(AYANAMSA_MODES)}")

    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    flags = swe.FLG_SIDEREAL | swe.FLG_MOSEPH | swe.FLG_SPEED
    jd = julian_day_utc(dt_utc)

    bodies = {}
    for name, code in _PLANET_CODES.items():
        longitude, retrograde = _planet_position(jd, code, flags)
        bodies[name] = _describe(longitude, retrograde)

    node_code = swe.TRUE_NODE if node_type == "true" else swe.MEAN_NODE
    rahu_longitude, rahu_retro = _planet_position(jd, node_code, flags)
    bodies["Rahu"] = _describe(rahu_longitude, True)
    bodies["Ketu"] = _describe((rahu_longitude + 180.0) % 360.0, True)

    _, ascmc = swe.houses_ex(jd, lat, lon, b"W", flags=swe.FLG_SIDEREAL)
    ascendant_longitude = ascmc[0]
    bodies["Ascendant"] = _describe(ascendant_longitude, False)

    return {
        "julian_day": jd,
        "ayanamsa": ayanamsa,
        "ayanamsa_value": swe.get_ayanamsa_ut(jd),
        "bodies": bodies,
    }


def saturn_sign_index(dt_utc: datetime, ayanamsa: str = "lahiri") -> int:
    """Fast path for repeated Saturn-only queries (e.g. a transit search),
    skipping the other 9 bodies and the Ascendant that compute_positions
    always computes.
    """
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    flags = swe.FLG_SIDEREAL | swe.FLG_MOSEPH
    jd = julian_day_utc(dt_utc)
    longitude, _ = _planet_position(jd, swe.SATURN, flags)
    return sign_index(longitude)


def _describe(longitude: float, retrograde: bool) -> dict:
    s_idx = sign_index(longitude)
    n_idx = nakshatra_index(longitude)
    nakshatra_offset = longitude % NAKSHATRA_SPAN
    return {
        "longitude": longitude,
        "sign": SIGN_NAMES[s_idx],
        "sign_index": s_idx,
        "degree_in_sign": longitude % SIGN_SPAN,
        "nakshatra": NAKSHATRA_NAMES[n_idx],
        "nakshatra_index": n_idx,
        "nakshatra_pada": int(nakshatra_offset // (NAKSHATRA_SPAN / 4)) + 1,
        "retrograde": retrograde,
    }
