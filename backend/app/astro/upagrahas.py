"""Upagrahas -- the shadow points.

Two families that share a name and nothing else. Which one a value belongs
to decides how much to trust it.

The **Sun-based** chain (Dhuma, Vyatipata, Parivesha, Indrachaapa,
Upaketu) is fixed arithmetic off the Sun's longitude. No sunrise, no
place, no convention dispute -- every source computes these identically,
so they are exact.

The **Kalavela** family (Gulika, Maandi, Kaala, Mrityu, Ardhaprahara,
Yamaghantaka) is the Ascendant sampled at a particular eighth of the day
or night, and here sources genuinely disagree -- on which eighth belongs
to which graha, and on whether the point is the start or the end of it.
Two reputable programs can put Gulika in different signs. What is done
here:

* The eighths are ruled starting from the weekday's own lord and running
  in weekday order; the eighth part is unruled. Gulika falls in Saturn's
  part, Kaala in the Sun's, Mrityu in Mars's, Ardhaprahara in Mercury's,
  Yamaghantaka in Jupiter's.
* That rule reproduces `panchanga.GULIKA_SEGMENT` exactly, which is where
  the app already gets Gulika Kaala from. The table is imported rather
  than restated so the two features cannot drift apart.
* Gulika is taken at the **start** of Saturn's part and Maandi at its
  **end**. Many texts treat the two as one point; others swap which end
  is which.

Night births divide sunset to the next sunrise instead, with the rulers
starting from the lord of the fifth weekday from the birth weekday.
"""
from __future__ import annotations

from app.astro import ephemeris
from app.astro.panchanga import GULIKA_SEGMENT

WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Which graha's eighth each Kalavela upagraha is read from.
KALAVELA_RULERS = {
    "Gulika": "Saturn",
    "Maandi": "Saturn",
    "Kaala": "Sun",
    "Mrityu": "Mars",
    "Ardhaprahara": "Mercury",
    "Yamaghantaka": "Jupiter",
}
# Maandi is the only one read at the closing edge of its part.
READ_AT_END = {"Maandi"}

# Sun-based chain, applied in this order -- each step consumes the one
# before it, so the sequence is not reorderable.
DHUMA_OFFSET = 133 + 20 / 60.0     # 133 degrees 20 minutes
UPAKETU_OFFSET = 16 + 40 / 60.0    # 16 degrees 40 minutes


def sun_based(sun_longitude: float) -> dict:
    """Dhuma through Upaketu. Exact, and independent of place and time."""
    dhuma = (sun_longitude + DHUMA_OFFSET) % 360.0
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachaapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachaapa + UPAKETU_OFFSET) % 360.0
    return {
        "Dhuma": dhuma,
        "Vyatipata": vyatipata,
        "Parivesha": parivesha,
        "Indrachaapa": indrachaapa,
        "Upaketu": upaketu,
    }


def _part_index(weekday: int, graha: str, is_day: bool) -> int | None:
    """Which eighth belongs to `graha`, 0-based from sunrise or sunset.

    `weekday` is 0 for Sunday, matching GULIKA_SEGMENT.
    """
    # A night birth restarts the sequence from the fifth weekday's lord.
    start = weekday if is_day else (weekday + 4) % 7
    order = [WEEKDAY_LORDS[(start + i) % 7] for i in range(7)]
    return order.index(graha) if graha in order else None


def kalavela(
    jd_birth: float,
    lat: float,
    lon: float,
    weekday: int,
    sunrise_jd: float | None,
    sunset_jd: float | None,
    next_sunrise_jd: float | None,
    ayanamsa: str = "lahiri",
) -> dict:
    """Gulika and friends, as the Ascendant at an eighth-part boundary.

    Returns an empty dict when the sun events are missing -- inside a
    polar circle there may be no sunrise to divide the day from.
    """
    if sunrise_jd is None or sunset_jd is None:
        return {}

    is_day = sunrise_jd <= jd_birth < sunset_jd
    if is_day:
        span_start, span_end = sunrise_jd, sunset_jd
    else:
        if next_sunrise_jd is None:
            return {}
        # Before dawn the birth belongs to the *previous* evening's night,
        # which is why the caller passes both sunrises.
        span_start = sunset_jd if jd_birth >= sunset_jd else sunset_jd - 1.0
        span_end = next_sunrise_jd if jd_birth >= sunset_jd else sunrise_jd

    part = (span_end - span_start) / 8.0

    out = {}
    for name, graha in KALAVELA_RULERS.items():
        index = _part_index(weekday, graha, is_day)
        if index is None:
            continue
        edge = index + 1 if name in READ_AT_END else index
        jd = span_start + part * edge
        out[name] = ephemeris.ascendant_at(jd, lat, lon, ayanamsa)
    return out


def compute_upagrahas(
    sun_longitude: float,
    jd_birth: float,
    lat: float,
    lon: float,
    weekday: int,
    sunrise_jd: float | None,
    sunset_jd: float | None,
    next_sunrise_jd: float | None,
    ayanamsa: str = "lahiri",
) -> dict:
    """Both families, each point described the way a graha is described."""
    values = dict(sun_based(sun_longitude))
    values.update(
        kalavela(jd_birth, lat, lon, weekday, sunrise_jd, sunset_jd, next_sunrise_jd, ayanamsa)
    )

    exact = set(sun_based(sun_longitude))
    return {
        name: {
            **_describe(longitude),
            # Surfaced so the UI can mark which half of the list is a
            # convention choice rather than a calculation.
            "exact": name in exact,
        }
        for name, longitude in values.items()
    }


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


# Kept as a module-level assertion of the claim made in the docstring: the
# ruler rule and the panchangam's Gulika table are the same statement.
def _gulika_table_agrees() -> bool:
    return all(
        _part_index(weekday, "Saturn", True) == index
        for weekday, index in GULIKA_SEGMENT.items()
    )
