"""Special lagnas -- alternative rising points used alongside the Ascendant.

Three groups, and they differ sharply in how much a small error in the
recorded birth time costs:

**Time-swept** (Bhava, Hora, Ghati, Vighati). Each starts from the Sun's
longitude at sunrise and advances at its own rate: one sign per five
ghatikas for Bhava, per two and a half for Hora, per one for Ghati, per
one *vighatika* for Vighati. A ghatika is 24 minutes. Bhava Lagna is
therefore forgiving, while Vighati Lagna moves a whole sign every 24
seconds -- it is reported here for completeness, but unless the birth
time is known to the second it is noise, and `stable` says so.

**Chart-derived** (Indu, Bhrigu Bindu, Sree, Kunda). Pure geometry off
positions already computed, so they are as good as the chart is.

Kunda multiplies the Ascendant by 81, which multiplies any error in the
Ascendant by 81 as well: a one-arcminute uncertainty in the birth time
becomes more than a degree here.
"""
from __future__ import annotations

from app.astro import ephemeris
from app.astro.matching import SIGN_LORDS

GHATIKA_DAYS = 24.0 / (60.0 * 24.0)  # one ghatika = 24 minutes, in days

# Signs advanced per ghatika elapsed since sunrise.
SWEEP_RATES = {
    "Bhava": 1.0 / 5.0,
    "Hora": 1.0 / 2.5,
    "Ghati": 1.0,
    "Vighati": 60.0,  # one sign per vighatika, and there are 60 to a ghatika
}
# Anything faster than a sign per few minutes cannot survive a birth time
# rounded to the nearest minute, let alone the nearest quarter hour.
UNSTABLE = {"Vighati"}

# Kalas contributed by each graha to the Indu Lagna sum.
INDU_KALAS = {
    "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
    "Jupiter": 10, "Venus": 12, "Saturn": 1,
}


def time_swept(jd_birth: float, sunrise_jd: float | None, ayanamsa: str = "lahiri") -> dict:
    """Bhava, Hora, Ghati and Vighati lagnas."""
    if sunrise_jd is None:
        return {}
    # A birth before dawn belongs to the previous sunrise, or every one of
    # these would come out negative.
    if jd_birth < sunrise_jd:
        sunrise_jd -= 1.0

    sun_at_sunrise = ephemeris.sun_longitude_at(sunrise_jd, ayanamsa)
    ghatikas = (jd_birth - sunrise_jd) / GHATIKA_DAYS

    return {
        name: (sun_at_sunrise + ghatikas * rate * 30.0) % 360.0
        for name, rate in SWEEP_RATES.items()
    }


def indu_lagna(bodies: dict) -> float:
    """Ninth lords from the Ascendant and from the Moon, summed as kalas.

    The remainder on division by twelve is counted from the Moon's sign
    inclusively, and the Moon's own degree is carried across.
    """
    asc_sign = bodies["Ascendant"]["sign_index"]
    moon_sign = bodies["Moon"]["sign_index"]

    ninth_from_lagna = SIGN_LORDS[(asc_sign + 8) % 12]
    ninth_from_moon = SIGN_LORDS[(moon_sign + 8) % 12]

    total = INDU_KALAS[ninth_from_lagna] + INDU_KALAS[ninth_from_moon]
    remainder = total % 12
    # A remainder of 0 lands on the twelfth sign, not the Moon's own.
    steps = (remainder - 1) % 12
    sign = (moon_sign + steps) % 12
    return sign * 30.0 + bodies["Moon"]["degree_in_sign"]


def bhrigu_bindu(bodies: dict) -> float:
    """Midpoint of Rahu and the Moon, measured forward from Rahu.

    Which of the two midpoints you get depends on the direction of travel,
    and they sit exactly opposite each other. Going forward from Rahu is
    the reading that matches the reference almanacs.
    """
    rahu = bodies["Rahu"]["longitude"]
    moon = bodies["Moon"]["longitude"]
    return (rahu + ((moon - rahu) % 360.0) / 2.0) % 360.0


def sree_lagna(bodies: dict) -> float:
    """Ascendant advanced by the Moon's progress through its nakshatra.

    A Moon at the very start of its nakshatra leaves Sree Lagna on the
    Ascendant; one at the end carries it a full circle round.
    """
    moon = bodies["Moon"]["longitude"]
    fraction = (moon % ephemeris.NAKSHATRA_SPAN) / ephemeris.NAKSHATRA_SPAN
    return (bodies["Ascendant"]["longitude"] + fraction * 360.0) % 360.0


def kunda_lagna(bodies: dict) -> float:
    """The Ascendant taken eighty-one times round the zodiac."""
    return (bodies["Ascendant"]["longitude"] * 81.0) % 360.0


def compute_special_lagnas(
    bodies: dict,
    jd_birth: float,
    sunrise_jd: float | None,
    ayanamsa: str = "lahiri",
) -> dict:
    values = dict(time_swept(jd_birth, sunrise_jd, ayanamsa))
    values["Pranapada"] = _pranapada(bodies, jd_birth, sunrise_jd, ayanamsa)
    values["Indu"] = indu_lagna(bodies)
    values["Bhrigu Bindu"] = bhrigu_bindu(bodies)
    values["Sree"] = sree_lagna(bodies)
    values["Kunda"] = kunda_lagna(bodies)

    return {
        name: {**_describe(longitude), "stable": name not in UNSTABLE}
        for name, longitude in values.items()
        if longitude is not None
    }


def _pranapada(bodies: dict, jd_birth: float, sunrise_jd: float | None, ayanamsa: str) -> float | None:
    """Sun advanced by the elapsed day, then shifted by the Sun's modality.

    The elapsed time since sunrise in vighatikas, divided by fifteen, is
    added to the Sun as degrees. The result is then thrown forward by a
    third or two thirds of the circle when the Sun sits in a fixed or
    dual sign -- movable signs take no shift.
    """
    if sunrise_jd is None:
        return None
    if jd_birth < sunrise_jd:
        sunrise_jd -= 1.0

    vighatikas = (jd_birth - sunrise_jd) / GHATIKA_DAYS * 60.0
    base = (bodies["Sun"]["longitude"] + vighatikas / 15.0) % 360.0

    modality = bodies["Sun"]["sign_index"] % 3  # 0 movable, 1 fixed, 2 dual
    shift = {0: 0.0, 1: 240.0, 2: 120.0}[modality]
    return (base + shift) % 360.0


def _describe(longitude: float) -> dict:
    s_idx = ephemeris.sign_index(longitude)
    n_idx = ephemeris.nakshatra_index(longitude)
    return {
        "longitude": longitude,
        "sign": ephemeris.SIGN_NAMES[s_idx],
        "sign_index": s_idx,
        "degree_in_sign": longitude % 30.0,
        "nakshatra": ephemeris.NAKSHATRA_NAMES[n_idx],
        "nakshatra_index": n_idx,
    }
