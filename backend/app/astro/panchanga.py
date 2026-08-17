"""Daily Panchangam -- the five limbs, plus sunrise/sunset and the
inauspicious periods a household actually checks before doing anything.

Unlike a birth chart, which someone computes once, a panchangam is a
daily reference. Everything here is derived from the Sun and Moon
positions the ephemeris already provides.

WHAT IS EXACT vs CONVENTIONAL
Tithi, vara, nakshatra, yoga and karana are pure arithmetic on the two
longitudes and are exact. Sunrise and sunset come from Swiss Ephemeris
with the standard refraction/disc-centre handling. Rahu Kalam,
Yamagandam, Gulika and Abhijit are unambiguous eighth/fifteenth divisions
of the day. Varjyam depends on a per-nakshatra table whose start values
differ slightly between almanacs -- it is included because it is one of
the most-consulted entries, and flagged in the API response so a caller
can present it accordingly.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone as _timezone

import swisseph as swe

UTC = _timezone.utc

from app.astro import ephemeris

# --- the five limbs ---------------------------------------------------

TITHI_NAMES = [
    "Padyami", "Vidiya", "Tadiya", "Chaviti", "Panchami", "Shashti",
    "Saptami", "Ashtami", "Navami", "Dasami", "Ekadasi", "Dwadasi",
    "Trayodasi", "Chaturdasi",
]
PAKSHA_NAMES = ["Shukla", "Krishna"]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra",
    "Vaidhriti",
]

KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
KARANA_FIXED = ["Shakuni", "Chatushpada", "Naga"]

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

TITHI_ARC = 12.0
YOGA_ARC = 360.0 / 27.0
KARANA_ARC = 6.0


def _sun_moon(jd: float, ayanamsa: str) -> tuple[float, float]:
    swe.set_sid_mode(ephemeris.AYANAMSA_MODES[ayanamsa])
    flags = swe.FLG_SIDEREAL | swe.FLG_MOSEPH
    sun, _ = swe.calc_ut(jd, swe.SUN, flags)
    moon, _ = swe.calc_ut(jd, swe.MOON, flags)
    return sun[0], moon[0]


def tithi_index(jd: float, ayanamsa: str) -> int:
    """0-29. The Sun/Moon difference is frame-independent, so the ayanamsa
    cancels out here -- it is passed only for consistency with the rest."""
    sun, moon = _sun_moon(jd, ayanamsa)
    return int(((moon - sun) % 360.0) // TITHI_ARC)


def yoga_index(jd: float, ayanamsa: str) -> int:
    """0-26. Unlike tithi this is a SUM, so it does depend on the frame and
    must be computed sidereally."""
    sun, moon = _sun_moon(jd, ayanamsa)
    return int(((sun + moon) % 360.0) // YOGA_ARC)


def karana_index(jd: float, ayanamsa: str) -> int:
    """0-59, a half-tithi."""
    sun, moon = _sun_moon(jd, ayanamsa)
    return int(((moon - sun) % 360.0) // KARANA_ARC)


def moon_nakshatra_index(jd: float, ayanamsa: str) -> int:
    _, moon = _sun_moon(jd, ayanamsa)
    return int((moon % 360.0) // ephemeris.NAKSHATRA_SPAN)


def describe_tithi(index: int) -> dict:
    paksha = 0 if index < 15 else 1
    within = index % 15
    if within == 14:
        name = "Pournami" if paksha == 0 else "Amavasya"
    else:
        name = TITHI_NAMES[within]
    return {
        "index": index,
        "number": within + 1,
        "name": name,
        "paksha": PAKSHA_NAMES[paksha],
        "paksha_index": paksha,
    }


def describe_karana(index: int) -> dict:
    # 60 half-tithis per lunar month: one fixed karana at the very start,
    # three at the very end, and the seven movable ones cycling between.
    if index == 0:
        name = "Kimstughna"
    elif index >= 57:
        name = KARANA_FIXED[index - 57]
    else:
        name = KARANA_MOVABLE[(index - 1) % 7]
    return {"index": index, "name": name}


# --- boundary search --------------------------------------------------

def _find_end(jd_start: float, index_fn, current: int, ayanamsa: str,
              max_days: float = 2.0) -> float | None:
    """Julian day at which `index_fn` stops returning `current`.

    Coarse scan then bisection. A limb can only advance, so the first hour
    whose index differs brackets the crossing.
    """
    step = 1.0 / 48.0  # 30 minutes
    lo = jd_start
    hi = jd_start + step
    limit = jd_start + max_days

    while hi <= limit:
        if index_fn(hi, ayanamsa) != current:
            for _ in range(40):  # ~0.03 s of precision
                mid = (lo + hi) / 2
                if index_fn(mid, ayanamsa) == current:
                    lo = mid
                else:
                    hi = mid
            return hi
        lo = hi
        hi += step
    return None


# --- sunrise / sunset -------------------------------------------------

def sun_events(jd_midnight_ut: float, lat: float, lon: float) -> tuple[float | None, float | None]:
    geopos = (lon, lat, 0.0)
    flags = swe.FLG_MOSEPH
    try:
        res_r, tret_r = swe.rise_trans(jd_midnight_ut, swe.SUN,
                                       swe.CALC_RISE | swe.BIT_DISC_CENTER,
                                       geopos, 0.0, 0.0, flags)
        res_s, tret_s = swe.rise_trans(jd_midnight_ut, swe.SUN,
                                       swe.CALC_SET | swe.BIT_DISC_CENTER,
                                       geopos, 0.0, 0.0, flags)
    except swe.Error:
        return None, None
    rise = tret_r[0] if res_r == 0 else None
    setting = tret_s[0] if res_s == 0 else None
    return rise, setting


# --- inauspicious / auspicious periods --------------------------------

# Daytime is split into eight equal parts; each weekday assigns one part to
# each of these. Indices are 0-based from sunrise, keyed by Python weekday
# convention with Sunday = 0.
RAHU_SEGMENT = {0: 7, 1: 1, 2: 6, 3: 4, 4: 5, 5: 3, 6: 2}
YAMA_SEGMENT = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 6, 6: 5}
GULIKA_SEGMENT = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}

# Ghatis from the start of the nakshatra at which varjyam begins. Almanacs
# differ by a ghati or two on several of these; see the module docstring.
VARJYAM_START_GHATIS = [
    50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 21,
    20, 14, 14, 10, 14, 56, 24, 20, 10, 10, 18, 16, 24, 30,
]
VARJYAM_LENGTH_GHATIS = 4.0
GHATIS_PER_NAKSHATRA = 60.0


def _eighth_part(sunrise: float, sunset: float, segment: int) -> tuple[float, float]:
    part = (sunset - sunrise) / 8.0
    return sunrise + part * segment, sunrise + part * (segment + 1)


def abhijit_muhurta(sunrise: float, sunset: float) -> tuple[float, float]:
    """The eighth of fifteen equal day divisions, straddling solar noon."""
    part = (sunset - sunrise) / 15.0
    return sunrise + part * 7, sunrise + part * 8


# A muhurta is a fifteenth of the day. Brahma Muhurta is the two that end
# at sunrise; Godhuli is the twilight straddling sunset.
MUHURTA_MINUTES = 48.0
GODHULI_HALF_MINUTES = 12.0


def brahma_muhurta(sunrise: float) -> tuple[float, float]:
    day = 1.0 / 1440.0
    return sunrise - 2 * MUHURTA_MINUTES * day, sunrise - MUHURTA_MINUTES * day


def godhuli_muhurta(sunset: float) -> tuple[float, float]:
    day = 1.0 / 1440.0
    return sunset - GODHULI_HALF_MINUTES * day, sunset + GODHULI_HALF_MINUTES * day


# Durmuhurta occupies particular muhurtas of the fifteen, by weekday.
# Some days carry two. Numbers are 1-based as they are usually tabulated.
DURMUHURTA_BY_WEEKDAY = {
    0: [14],        # Sunday
    1: [9, 12],     # Monday
    2: [4],         # Tuesday
    3: [8],         # Wednesday -- collides with Abhijit, which is why
    4: [6, 12],     # Abhijit is held to be inauspicious on a Wednesday
    5: [5, 9],      # Friday
    6: [2],         # Saturday
}

# The direction to avoid travelling in, by weekday.
DISHASHOOL_BY_WEEKDAY = {
    0: "West", 1: "East", 2: "North", 3: "North",
    4: "South", 5: "West", 6: "East",
}


def durmuhurta_windows(sunrise: float, sunset: float, weekday: int) -> list[tuple[float, float]]:
    part = (sunset - sunrise) / 15.0
    return [
        (sunrise + part * (n - 1), sunrise + part * n)
        for n in DURMUHURTA_BY_WEEKDAY[weekday]
    ]


# --- lunar month, phase and events ---------------------------------------

# Amanta reckoning (month ends at Amavasya), which is what is used across
# the south. Purnimanta reckoning, common in the north, names the same day
# differently for the dark fortnight -- worth knowing if a reader compares
# against a northern almanac.
MASA_BY_SUN_SIGN_AT_NEW_MOON = [
    "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwina",
    "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna", "Chaitra",
]

MOON_PHASES = [
    (0, 6, "Shukla Ardhachandra", "Waxing Crescent"),
    (7, 7, "Shukla Ashtami", "First Quarter"),
    (8, 13, "Shukla Purna", "Waxing Gibbous"),
    (14, 14, "Purnima", "Full Moon"),
    (15, 21, "Krishna Purna", "Waning Gibbous"),
    (22, 22, "Krishna Ashtami", "Last Quarter"),
    (23, 28, "Krishna Ardhachandra", "Waning Crescent"),
    (29, 29, "Amavasya", "New Moon"),
]


def moon_phase(tithi_idx: int) -> dict:
    for lo, hi, name, english in MOON_PHASES:
        if lo <= tithi_idx <= hi:
            return {"name": name, "english": english}
    return {"name": "", "english": ""}


def moon_events(jd_midnight_ut: float, lat: float, lon: float) -> tuple[float | None, float | None]:
    """Moonrise and moonset. Either can be absent on a given day, because
    the Moon rises roughly 50 minutes later each day and so skips one."""
    geopos = (lon, lat, 0.0)
    flags = swe.FLG_MOSEPH
    rise = setting = None
    try:
        res, tret = swe.rise_trans(jd_midnight_ut, swe.MOON, swe.CALC_RISE, geopos, 0.0, 0.0, flags)
        if res == 0:
            rise = tret[0]
        res, tret = swe.rise_trans(jd_midnight_ut, swe.MOON, swe.CALC_SET, geopos, 0.0, 0.0, flags)
        if res == 0:
            setting = tret[0]
    except swe.Error:
        pass
    return rise, setting


def last_new_moon(jd: float, ayanamsa: str) -> float:
    """Julian day of the Amavasya that began the current lunar month.

    Steps back a day at a time until the elongation stops decreasing, then
    bisects. A lunar month is ~29.5 days, so 32 bounds the search.
    """
    elongation = lambda t: (_sun_moon(t, ayanamsa)[1] - _sun_moon(t, ayanamsa)[0]) % 360.0
    lo = jd
    for _ in range(32):
        prev = lo - 1.0
        if elongation(prev) > elongation(lo):
            hi = lo
            lo = prev
            for _ in range(40):
                mid = (lo + hi) / 2
                if elongation(mid) > elongation(hi):
                    lo = mid
                else:
                    hi = mid
            return hi
        lo = prev
    return jd


def masa(jd: float, ayanamsa: str) -> dict:
    """The lunar month, named from the Sun's sign at the new moon that
    started it."""
    new_moon_jd = last_new_moon(jd, ayanamsa)
    sun_longitude, _ = _sun_moon(new_moon_jd, ayanamsa)
    sign = ephemeris.sign_index(sun_longitude)
    return {"name": MASA_BY_SUN_SIGN_AT_NEW_MOON[sign], "sun_sign_index": sign}


def varjyam_window(nak_start_jd: float, nak_end_jd: float, nak_index: int) -> tuple[float, float]:
    span = nak_end_jd - nak_start_jd
    start = nak_start_jd + span * (VARJYAM_START_GHATIS[nak_index] / GHATIS_PER_NAKSHATRA)
    end = start + span * (VARJYAM_LENGTH_GHATIS / GHATIS_PER_NAKSHATRA)
    return start, end


# --- assembly ---------------------------------------------------------

def _jd_to_local(jd: float | None, tz) -> str | None:
    """Julian day (UT) -> local wall-clock HH:MM in the given timezone."""
    if jd is None:
        return None
    y, m, d, hour = swe.revjul(jd)
    base = datetime(y, m, d) + timedelta(hours=hour)
    return base.replace(tzinfo=UTC).astimezone(tz).strftime("%H:%M")


# Festivals that follow directly from masa, paksha and tithi. Deliberately
# a short list: most of the calendar is regional, and a wrong festival date
# is worse than an absent one. Keyed (masa or None for monthly, paksha,
# tithi-within-paksha 1-15).
FESTIVAL_RULES = [
    ("Ugadi", "Chaitra", "Shukla", 1, "Festival"),
    ("Akshaya Tritiya", "Vaishakha", "Shukla", 3, "Festival"),
    ("Nag Panchami", "Shravana", "Shukla", 5, "Festival"),
    ("Varalakshmi Vratam", "Shravana", "Shukla", 12, "Vrat"),
    ("Ganesh Chaturthi", "Bhadrapada", "Shukla", 4, "Festival"),
    ("Vijaya Dashami", "Ashwina", "Shukla", 10, "Festival"),
    ("Deepavali", "Kartika", "Krishna", 15, "Festival"),
    ("Maha Shivaratri", "Magha", "Krishna", 14, "Festival"),
    # Monthly observances, any masa.
    ("Ekadashi", None, "Shukla", 11, "Vrat"),
    ("Ekadashi", None, "Krishna", 11, "Vrat"),
    ("Pradosham", None, "Shukla", 13, "Vrat"),
    ("Pradosham", None, "Krishna", 13, "Vrat"),
    ("Vinayaka Chaturthi", None, "Shukla", 4, "Vrat"),
    ("Sankashti Chaturthi", None, "Krishna", 4, "Vrat"),
    ("Purnima", None, "Shukla", 15, "Observance"),
    ("Amavasya", None, "Krishna", 15, "Observance"),
]


def festivals(masa_name: str, paksha: str, tithi_number: int) -> list[dict]:
    named = [
        {"name": name, "kind": kind, "major": required_masa is not None}
        for name, required_masa, required_paksha, number, kind in FESTIVAL_RULES
        if required_paksha == paksha
        and number == tithi_number
        and (required_masa is None or required_masa == masa_name)
    ]
    # A dated festival outranks the monthly observance sharing its tithi.
    return sorted(named, key=lambda f: not f["major"])


def sankranti(jd_sunrise: float, ayanamsa: str) -> dict | None:
    """Whether the Sun changes sign during this day, and into which."""
    before, _ = _sun_moon(jd_sunrise - 0.5, ayanamsa)
    after, _ = _sun_moon(jd_sunrise + 0.5, ayanamsa)
    if ephemeris.sign_index(before) == ephemeris.sign_index(after):
        return None
    entering = ephemeris.sign_index(after)
    return {"sign_index": entering, "sign": ephemeris.SIGN_NAMES[entering]}


def _limb(jd_ref: float, index_fn, describe, ayanamsa: str, tz) -> dict:
    """A limb's value at the reference moment, plus when it gives way.

    Panchangam convention reads the limbs as they stand at sunrise and
    reports the moment each ends, which is why the day's tithi can differ
    from the one in force at, say, noon.
    """
    index = index_fn(jd_ref, ayanamsa)
    end_jd = _find_end(jd_ref, index_fn, index, ayanamsa)
    out = describe(index)
    out["ends_at"] = _jd_to_local(end_jd, tz)
    out["ends_jd"] = end_jd
    return out


def _limb_sequence(jd_start: float, jd_limit: float, index_fn, describe,
                   ayanamsa: str, tz, cap: int = 4) -> list[dict]:
    """Every value of a limb in force between sunrise and the next sunrise.

    An almanac lists what is running now and what follows, because a tithi
    that ends mid-afternoon is only half the day's story. Karana moves
    fastest and usually gives three entries; tithi and yoga give one or two.
    """
    out = []
    cursor = jd_start

    for _ in range(cap):
        index = index_fn(cursor, ayanamsa)
        end_jd = _find_end(cursor, index_fn, index, ayanamsa)
        entry = describe(index)
        entry["ends_at"] = _jd_to_local(end_jd, tz)
        entry["ends_jd"] = end_jd
        out.append(entry)
        if end_jd is None or end_jd >= jd_limit:
            break
        cursor = end_jd + 1e-6

    return out


def compute_panchanga(local_date, lat: float, lon: float, tz, ayanamsa: str = "lahiri") -> dict:
    """Full panchangam for a calendar date at a place.

    `tz` is a pytz timezone; `local_date` a datetime.date in that zone.
    """
    midnight_local = tz.localize(datetime(local_date.year, local_date.month, local_date.day))
    jd_midnight = ephemeris.julian_day_utc(midnight_local)

    sunrise, sunset = sun_events(jd_midnight, lat, lon)
    # Everything is read at sunrise, per convention; without one (polar
    # day/night) fall back to local midnight so the limbs still resolve.
    jd_ref = sunrise if sunrise is not None else jd_midnight

    # Two different windows on purpose.
    #
    # The day's anga -- the one a festival or varjyam is keyed to -- is
    # whatever is in force at SUNRISE, which is the traditional rule.
    #
    # The listing, though, runs the calendar day from MIDNIGHT, so an
    # almanac shows the nakshatra that was still running before dawn as
    # well as the one that takes over. Reading only from sunrise silently
    # drops that first entry, and the page then disagrees with every
    # printed panchangam for the first few hours of the day.
    yoga_desc = lambda i: {"index": i, "name": YOGA_NAMES[i]}
    nak_desc = lambda i: {"index": i, "name": ephemeris.NAKSHATRA_NAMES[i]}

    tithi = _limb(jd_ref, tithi_index, describe_tithi, ayanamsa, tz)
    yoga = _limb(jd_ref, yoga_index, yoga_desc, ayanamsa, tz)
    karana = _limb(jd_ref, karana_index, describe_karana, ayanamsa, tz)
    nak = _limb(jd_ref, moon_nakshatra_index, nak_desc, ayanamsa, tz)

    day_end = jd_midnight + 1.0
    tithis = _limb_sequence(jd_midnight, day_end, tithi_index, describe_tithi, ayanamsa, tz, cap=3)
    yogas = _limb_sequence(jd_midnight, day_end, yoga_index, yoga_desc, ayanamsa, tz, cap=3)
    karanas = _limb_sequence(jd_midnight, day_end, karana_index, describe_karana, ayanamsa, tz, cap=4)
    naks = _limb_sequence(jd_midnight, day_end, moon_nakshatra_index, nak_desc, ayanamsa, tz, cap=3)
    weekday = (midnight_local.weekday() + 1) % 7  # Python Mon=0 -> Sunday=0

    periods = {}
    if sunrise is not None and sunset is not None:
        def window(pair):
            return {"start": _jd_to_local(pair[0], tz), "end": _jd_to_local(pair[1], tz)}

        periods["rahu_kalam"] = window(_eighth_part(sunrise, sunset, RAHU_SEGMENT[weekday]))
        periods["yamagandam"] = window(_eighth_part(sunrise, sunset, YAMA_SEGMENT[weekday]))
        periods["gulika_kalam"] = window(_eighth_part(sunrise, sunset, GULIKA_SEGMENT[weekday]))
        periods["abhijit"] = window(abhijit_muhurta(sunrise, sunset))
        periods["brahma"] = window(brahma_muhurta(sunrise))
        periods["godhuli"] = window(godhuli_muhurta(sunset))
        periods["durmuhurta"] = [window(w) for w in durmuhurta_windows(sunrise, sunset, weekday)]

        # Varjyam needs the nakshatra's own span, not the solar day's.
        nak_start = _find_start(jd_ref, moon_nakshatra_index, nak["index"], ayanamsa)
        if nak_start is not None and nak["ends_jd"] is not None:
            periods["varjyam"] = window(varjyam_window(nak_start, nak["ends_jd"], nak["index"]))

    moonrise, moonset = moon_events(jd_midnight, lat, lon)
    sun_longitude, moon_longitude = _sun_moon(jd_ref, ayanamsa)
    sun_sign = ephemeris.sign_index(sun_longitude)
    moon_sign = ephemeris.sign_index(moon_longitude)

    # Lagna at sunrise -- the sign rising as the day begins.
    swe.set_sid_mode(ephemeris.AYANAMSA_MODES[ayanamsa])
    _, ascmc = swe.houses_ex(jd_ref, lat, lon, b"W", flags=swe.FLG_SIDEREAL)
    lagna_sign = ephemeris.sign_index(ascmc[0])

    month = masa(jd_ref, ayanamsa)
    day_length_minutes = (
        round((sunset - sunrise) * 1440) if sunrise is not None and sunset is not None else None
    )

    for limb in tithis + yogas + karanas + naks + [tithi, yoga, karana, nak]:
        limb.pop("ends_jd", None)

    return {
        "date": local_date.isoformat(),
        "vara": {"index": weekday, "name": VARA_NAMES[weekday]},
        "masa": month,
        "tithi": tithi,
        "nakshatra": nak,
        "yoga": yoga,
        "karana": karana,
        # The full run across the almanac day, so a card can show what
        # follows rather than only what is in force at sunrise.
        "tithis": tithis,
        "nakshatras": naks,
        "yogas": yogas,
        "karanas": karanas,
        "sunrise": _jd_to_local(sunrise, tz),
        "sunset": _jd_to_local(sunset, tz),
        "moonrise": _jd_to_local(moonrise, tz),
        "moonset": _jd_to_local(moonset, tz),
        "day_length_minutes": day_length_minutes,
        "sun_sign": {"index": sun_sign, "name": ephemeris.SIGN_NAMES[sun_sign]},
        "moon_sign": {"index": moon_sign, "name": ephemeris.SIGN_NAMES[moon_sign]},
        "lagna": {"index": lagna_sign, "name": ephemeris.SIGN_NAMES[lagna_sign]},
        "moon_phase": moon_phase(tithi["index"]),
        "dishashool": DISHASHOOL_BY_WEEKDAY[weekday],
        "festivals": festivals(month["name"], tithi["paksha"], tithi["number"]),
        "sankranti": sankranti(jd_ref, ayanamsa),
        "periods": periods,
        "varjyam_is_conventional": True,
    }


def _find_start(jd_ref: float, index_fn, current: int, ayanamsa: str,
                max_days: float = 2.0) -> float | None:
    """Mirror of _find_end, searching backwards for where `current` began."""
    step = 1.0 / 48.0
    hi = jd_ref
    lo = jd_ref - step
    limit = jd_ref - max_days

    while lo >= limit:
        if index_fn(lo, ayanamsa) != current:
            for _ in range(40):
                mid = (lo + hi) / 2
                if index_fn(mid, ayanamsa) == current:
                    hi = mid
                else:
                    lo = mid
            return hi
        hi = lo
        lo -= step
    return None
