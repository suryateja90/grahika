"""Shadbala -- the six-fold strength of a graha, in virupas.

READ THIS BEFORE TRUSTING THE NUMBERS.

Shadbala is the heaviest calculation in Jyotish and the one where sources
disagree most. Six components, several of which are themselves sums of
four or five sub-parts, and almost every sub-part has a variant somewhere.
Two reputable programs routinely differ by tens of virupas on the same
chart. So rather than present a single figure as settled, each component
is returned separately, and this docstring says plainly which are exact
and which are not.

EXACT -- one accepted definition, implemented in full:
  Naisargika (natural)      fixed per graha
  Dig (directional)         angular distance from the weak point
  Uchcha (part of Sthana)   distance from the debilitation degree
  Kendradi, Ojhayugma       house class, odd/even sign and navamsa
  Paksha, Nathonnatha       lunar phase and day/night, part of Kala

APPROXIMATED -- a defensible reading among several:
  Saptavargaja  dignity across seven vargas, using the same natural
                friendship table Kundli Matching uses; temporal
                friendship is NOT folded in
  Cheshta       from actual vs mean daily motion mapped onto the eight
                classical motion states, rather than the arc-based method
  Drik          Parashari drishti by house distance, benefic positive and
                malefic negative; the degree-scaled drishti curve is not
                applied
  Kala          Abda and Masa Bala are omitted; Tribhaga, Vara and Hora
                are included

NOT IMPLEMENTED:
  Yuddha Bala (planetary war) -- applies only when two grahas sit within
  one degree, and changes the result rarely enough that a wrong
  implementation would do more harm than its absence.

Treat the total as indicative and the components as the useful output.
"""
from __future__ import annotations

import math
from datetime import datetime

import swisseph as swe

from app.astro import ephemeris
from app.astro.matching import PLANET_ENEMIES, PLANET_FRIENDS, SIGN_LORDS

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Strength a graha needs to count as strong, in rupas (1 rupa = 60 virupas).
REQUIRED_RUPAS = {
    "Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0,
}
VIRUPAS_PER_RUPA = 60.0

# Fixed by nature, evenly spaced between Saturn and the Sun.
NAISARGIKA = {
    "Saturn": 8.57, "Mars": 17.14, "Mercury": 25.71, "Jupiter": 34.29,
    "Venus": 42.86, "Moon": 51.43, "Sun": 60.0,
}

# Exaltation degree; debilitation sits opposite.
EXALTATION = {
    "Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
    "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0,
}

# House in which each graha has full directional strength.
DIG_STRONG_HOUSE = {
    "Jupiter": 1, "Mercury": 1, "Sun": 10, "Mars": 10,
    "Moon": 4, "Venus": 4, "Saturn": 7,
}

OWN_SIGNS = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
    "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
}
# sign index, start degree, end degree
MOOLATRIKONA = {
    "Sun": (4, 0, 20), "Moon": (1, 4, 30), "Mars": (0, 0, 12),
    "Mercury": (5, 16, 20), "Jupiter": (8, 0, 10), "Venus": (6, 0, 15),
    "Saturn": (10, 0, 20),
}

SAPTAVARGA = ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]
DIGNITY_VIRUPAS = {
    "moolatrikona": 45.0, "own": 30.0, "great_friend": 22.5, "friend": 15.0,
    "neutral": 7.5, "enemy": 3.75, "great_enemy": 1.875,
}

BENEFICS = {"Jupiter", "Venus"}          # Mercury and the Moon are conditional
MALEFICS = {"Sun", "Mars", "Saturn"}

# Mean daily motion, degrees. Used to place a graha among the eight
# classical motion states for Cheshta Bala.
MEAN_SPEED = {
    "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524, "Mercury": 1.383,
    "Jupiter": 0.083, "Venus": 1.602, "Saturn": 0.0335,
}

WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
# The hora sequence runs in Chaldean order from the weekday's lord.
HORA_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]


def _uchcha_bala(name: str, longitude: float) -> float:
    """Distance from the debilitation point, 0 there and 60 at exaltation."""
    debilitation = (EXALTATION[name] + 180.0) % 360.0
    separation = abs(longitude - debilitation) % 360.0
    if separation > 180.0:
        separation = 360.0 - separation
    return separation / 3.0


def _dignity(name: str, sign: int, degree: float, is_rasi: bool) -> str:
    if is_rasi:
        moola_sign, lo, hi = MOOLATRIKONA[name]
        if sign == moola_sign and lo <= degree < hi:
            return "moolatrikona"
    if sign in OWN_SIGNS[name]:
        return "own"

    lord = SIGN_LORDS[sign]
    if lord == name:
        return "own"
    if lord in PLANET_FRIENDS[name]:
        return "friend"
    if lord in PLANET_ENEMIES[name]:
        return "enemy"
    return "neutral"


def _saptavargaja_bala(name: str, varga_signs: dict, degree: float) -> float:
    total = 0.0
    for code in SAPTAVARGA:
        sign = varga_signs[code]["sign_index"]
        total += DIGNITY_VIRUPAS[_dignity(name, sign, degree, code == "D1")]
    return total


def _ojhayugma_bala(name: str, rasi: int, navamsa: int) -> float:
    """15 virupas each for sitting in the parity of sign the graha prefers:
    Moon and Venus the even signs, the rest the odd."""
    prefers_even = name in ("Moon", "Venus")
    total = 0.0
    for sign in (rasi, navamsa):
        is_even = sign % 2 == 1  # 0-indexed Aries is the 1st, an odd sign
        if is_even == prefers_even:
            total += 15.0
    return total


def _kendradi_bala(house: int) -> float:
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana_bala(name: str, degree: float) -> float:
    """15 virupas for the third of a sign matching the graha's gender:
    male in the first, hermaphrodite the second, female the third."""
    third = int(degree // 10.0)
    male = {"Sun", "Mars", "Jupiter"}
    female = {"Moon", "Venus"}
    if name in male and third == 0:
        return 15.0
    if name in female and third == 2:
        return 15.0
    if name not in male and name not in female and third == 1:
        return 15.0
    return 0.0


def _dig_bala(name: str, longitude: float, asc_longitude: float) -> float:
    strong_cusp = (asc_longitude + (DIG_STRONG_HOUSE[name] - 1) * 30.0) % 360.0
    weak_cusp = (strong_cusp + 180.0) % 360.0
    separation = abs(longitude - weak_cusp) % 360.0
    if separation > 180.0:
        separation = 360.0 - separation
    return separation / 3.0


def _nathonnatha_bala(name: str, hours_from_midnight: float) -> float:
    """Day/night strength. Mercury is strong at all hours."""
    if name == "Mercury":
        return 60.0
    # Distance from midnight, 0 at midnight and 12 at noon.
    from_midnight = abs(hours_from_midnight)
    if from_midnight > 12.0:
        from_midnight = 24.0 - from_midnight
    diurnal = from_midnight * 5.0            # 60 at noon
    nocturnal = 60.0 - diurnal               # 60 at midnight
    return nocturnal if name in ("Moon", "Mars", "Saturn") else diurnal


def _paksha_bala(name: str, sun_longitude: float, moon_longitude: float) -> float:
    """From the Moon's elongation: benefics gain as it waxes, malefics as
    it wanes. The Moon's own value is doubled."""
    elongation = (moon_longitude - sun_longitude) % 360.0
    if elongation > 180.0:
        elongation = 360.0 - elongation
    waxing_strength = elongation / 3.0       # 0 at new moon, 60 at full

    benefic = name in BENEFICS or name == "Moon" or (
        name == "Mercury" and True  # Mercury counts benefic when unafflicted
    )
    value = waxing_strength if benefic else 60.0 - waxing_strength
    return value * 2.0 if name == "Moon" else value


def _tribhaga_bala(name: str, is_daytime: bool, fraction: float) -> float:
    """60 virupas to one graha per third of the day, and to Jupiter always."""
    if name == "Jupiter":
        return 60.0
    third = min(2, int(fraction * 3))
    day_lords = ["Mercury", "Sun", "Saturn"]
    night_lords = ["Moon", "Venus", "Mars"]
    lords = day_lords if is_daytime else night_lords
    return 60.0 if lords[third] == name else 0.0


def _vara_hora_bala(name: str, weekday: int, hours_from_sunrise: float) -> float:
    """45 virupas to the lord of the weekday, 60 to the lord of the hour."""
    total = 0.0
    if WEEKDAY_LORDS[weekday] == name:
        total += 45.0
    day_lord = WEEKDAY_LORDS[weekday]
    start = HORA_ORDER.index(day_lord)
    hora = int(hours_from_sunrise) % 24
    if HORA_ORDER[(start + hora) % 7] == name:
        total += 60.0
    return total


def _ayana_bala(name: str, declination: float) -> float:
    """From declination. Most grahas gain in northern declination; the Moon
    and Saturn in southern. The Sun's value is doubled."""
    northward = name not in ("Moon", "Saturn")
    signed = declination if northward else -declination
    value = (signed + 24.0) / 48.0 * 60.0
    value = max(0.0, min(60.0, value))
    return value * 2.0 if name == "Sun" else value


def _cheshta_bala(name: str, speed: float) -> float:
    """From actual against mean motion, mapped onto the classical states.

    The arc-based method computes a true Cheshta Kendra; this reads the
    same states off the speed instead, which is the common computational
    shortcut and agrees on the ordering if not always the exact virupas.
    """
    if name == "Sun":
        return 0.0   # supplied by Ayana Bala instead
    if name == "Moon":
        return 0.0   # supplied by Paksha Bala instead

    mean = MEAN_SPEED[name]
    if speed < 0:
        return 60.0 if abs(speed) > mean * 0.3 else 30.0   # vakra / anuvakra
    if speed < mean * 0.25:
        return 15.0          # vikala, near stationary
    if speed < mean * 0.75:
        return 30.0          # manda
    if speed < mean * 1.25:
        return 7.5           # sama
    if speed < mean * 1.75:
        return 45.0          # chara
    return 30.0              # atichara


# Drishti by house distance, Parashari special aspects included.
SPECIAL_DRISHTI = {
    "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10],
}


def _drik_bala(name: str, bodies: dict) -> float:
    """Benefic aspects add, malefic aspects subtract.

    The classical method scales each aspect by a degree-based drishti
    curve; this uses whole-sign Parashari aspects at full value, so the
    magnitude is coarser than the sign.
    """
    target_sign = bodies[name]["sign_index"]
    total = 0.0
    for other in GRAHAS:
        if other == name:
            continue
        from_sign = bodies[other]["sign_index"]
        distance = ((target_sign - from_sign) % 12) + 1
        casts = SPECIAL_DRISHTI.get(other, [7])
        if distance not in casts:
            continue
        if other in MALEFICS:
            total -= 15.0
        elif other in BENEFICS or other == "Moon":
            total += 15.0
    return total


def compute_shadbala(bodies: dict, vargas_by_body: dict, birth_dt: datetime,
                     jd: float, sunrise_jd: float | None, ayanamsa: str) -> dict:
    """All six strengths per graha, in virupas."""
    asc_longitude = bodies["Ascendant"]["longitude"]
    asc_sign = bodies["Ascendant"]["sign_index"]
    sun_longitude = bodies["Sun"]["longitude"]
    moon_longitude = bodies["Moon"]["longitude"]

    hours_from_midnight = birth_dt.hour + birth_dt.minute / 60 + birth_dt.second / 3600
    weekday = (birth_dt.weekday() + 1) % 7
    hours_from_sunrise = (
        (jd - sunrise_jd) * 24.0 if sunrise_jd is not None else hours_from_midnight - 6.0
    )
    is_daytime = 6.0 <= hours_from_midnight < 18.0
    day_fraction = ((hours_from_midnight - 6.0) / 12.0) if is_daytime else (
        ((hours_from_midnight + 6.0) % 24.0) / 12.0
    )

    swe.set_sid_mode(ephemeris.AYANAMSA_MODES[ayanamsa])
    flags = swe.FLG_SIDEREAL | swe.FLG_MOSEPH | swe.FLG_SPEED | swe.FLG_EQUATORIAL

    out = {}
    for name in GRAHAS:
        body = bodies[name]
        longitude = body["longitude"]
        degree = body["degree_in_sign"]
        sign = body["sign_index"]
        house = ((sign - asc_sign) % 12) + 1

        equatorial, _ = swe.calc_ut(jd, ephemeris._PLANET_CODES[name], flags)
        declination = equatorial[1]
        speed = body.get("speed", 0.0)

        sthana = (
            _uchcha_bala(name, longitude)
            + _saptavargaja_bala(name, vargas_by_body[name], degree)
            + _ojhayugma_bala(name, sign, vargas_by_body[name]["D9"]["sign_index"])
            + _kendradi_bala(house)
            + _drekkana_bala(name, degree)
        )
        dig = _dig_bala(name, longitude, asc_longitude)
        kala = (
            _nathonnatha_bala(name, hours_from_midnight)
            + _paksha_bala(name, sun_longitude, moon_longitude)
            + _tribhaga_bala(name, is_daytime, day_fraction)
            + _vara_hora_bala(name, weekday, hours_from_sunrise)
            + _ayana_bala(name, declination)
        )
        cheshta = _cheshta_bala(name, speed)
        naisargika = NAISARGIKA[name]
        drik = _drik_bala(name, bodies)

        total = sthana + dig + kala + cheshta + naisargika + drik
        required = REQUIRED_RUPAS[name] * VIRUPAS_PER_RUPA

        out[name] = {
            "sthana": round(sthana, 2),
            "dig": round(dig, 2),
            "kala": round(kala, 2),
            "cheshta": round(cheshta, 2),
            "naisargika": round(naisargika, 2),
            "drik": round(drik, 2),
            "total": round(total, 2),
            "required": round(required, 2),
            "ratio": round(total / required, 3) if required else 0.0,
            "strong": total >= required,
        }

    ranked = sorted(out, key=lambda n: out[n]["ratio"], reverse=True)
    for position, name in enumerate(ranked, start=1):
        out[name]["rank"] = position

    return out
