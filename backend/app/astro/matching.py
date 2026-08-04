"""Ashtakoot (Guna Milan) compatibility matching -- the 36-point system.

Eight kootas, weighted 1+2+3+4+5+6+7+8 = 36. All eight derive from just
the Moon's sign and nakshatra of each person, which is why matching needs
far less input than a full chart. Mangal Dosha (Manglik) is computed
separately from the Ascendant, and is conventionally reported alongside
the score rather than folded into it.

ON ACCURACY -- read before trusting output:
Unlike planetary positions (which are pure astronomy and match reference
sites to within arcseconds), Guna Milan tables genuinely vary between
lineages and between commercial software. Where a table is unambiguous
and universally agreed (Nadi, Bhakoot, Gana, Varna, Tara) this module
implements it exactly. Where published tables disagree, the choice made
here is documented inline at the point of the decision. The Yoni koota's
intermediate gradations are explicitly simplified -- see YONI_* below.

Expect small per-koota differences against AstroSage/Prokerala. Large
differences (>2 points total) indicate a bug worth investigating.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Varna (1 point) -- priestly/warrior/merchant/servant class from Moon sign.
# Unambiguous across sources: water=Brahmin, fire=Kshatriya, earth=Vaishya,
# air=Shudra. Point awarded only if the groom's varna is not lower than the
# bride's.
# ---------------------------------------------------------------------------
VARNA_BY_SIGN = [
    "Kshatriya",  # Aries (fire)
    "Vaishya",    # Taurus (earth)
    "Shudra",     # Gemini (air)
    "Brahmin",    # Cancer (water)
    "Kshatriya",  # Leo (fire)
    "Vaishya",    # Virgo (earth)
    "Shudra",     # Libra (air)
    "Brahmin",    # Scorpio (water)
    "Kshatriya",  # Sagittarius (fire)
    "Vaishya",    # Capricorn (earth)
    "Shudra",     # Aquarius (air)
    "Brahmin",    # Pisces (water)
]
VARNA_RANK = {"Shudra": 1, "Vaishya": 2, "Kshatriya": 3, "Brahmin": 4}


def varna_koota(bride_moon_sign: int, groom_moon_sign: int) -> dict:
    bride_varna = VARNA_BY_SIGN[bride_moon_sign]
    groom_varna = VARNA_BY_SIGN[groom_moon_sign]
    score = 1.0 if VARNA_RANK[groom_varna] >= VARNA_RANK[bride_varna] else 0.0
    return {
        "name": "Varna",
        "max": 1,
        "score": score,
        "bride": bride_varna,
        "groom": groom_varna,
    }


# ---------------------------------------------------------------------------
# Vashya (2 points) -- mutual control/magnetism group.
# Sagittarius and Capricorn are split by half in strict treatments (first
# half one group, second half another). This module uses whole-sign
# assignment, the common simplification in software implementations.
# ---------------------------------------------------------------------------
VASHYA_BY_SIGN = [
    "Chatushpada",  # Aries
    "Chatushpada",  # Taurus
    "Manava",       # Gemini
    "Jalachara",    # Cancer
    "Vanachara",    # Leo
    "Manava",       # Virgo
    "Manava",       # Libra
    "Keeta",        # Scorpio
    "Manava",       # Sagittarius (strictly: 1st half Manava, 2nd Chatushpada)
    "Jalachara",    # Capricorn (strictly: 1st half Chatushpada, 2nd Jalachara)
    "Manava",       # Aquarius
    "Jalachara",    # Pisces
]

VASHYA_MATRIX = {
    ("Chatushpada", "Chatushpada"): 2.0,
    ("Chatushpada", "Manava"): 1.0,
    ("Chatushpada", "Jalachara"): 1.0,
    ("Chatushpada", "Vanachara"): 0.0,
    ("Chatushpada", "Keeta"): 1.0,
    ("Manava", "Manava"): 2.0,
    ("Manava", "Chatushpada"): 1.0,
    ("Manava", "Jalachara"): 0.5,
    ("Manava", "Vanachara"): 0.0,
    ("Manava", "Keeta"): 1.0,
    ("Jalachara", "Jalachara"): 2.0,
    ("Jalachara", "Chatushpada"): 1.0,
    ("Jalachara", "Manava"): 0.5,
    ("Jalachara", "Vanachara"): 1.0,
    ("Jalachara", "Keeta"): 1.0,
    ("Vanachara", "Vanachara"): 2.0,
    ("Vanachara", "Chatushpada"): 0.0,
    ("Vanachara", "Manava"): 0.0,
    ("Vanachara", "Jalachara"): 1.0,
    ("Vanachara", "Keeta"): 1.0,
    ("Keeta", "Keeta"): 2.0,
    ("Keeta", "Chatushpada"): 1.0,
    ("Keeta", "Manava"): 1.0,
    ("Keeta", "Jalachara"): 1.0,
    ("Keeta", "Vanachara"): 1.0,
}


def vashya_koota(bride_moon_sign: int, groom_moon_sign: int) -> dict:
    bride_vashya = VASHYA_BY_SIGN[bride_moon_sign]
    groom_vashya = VASHYA_BY_SIGN[groom_moon_sign]
    score = VASHYA_MATRIX.get((groom_vashya, bride_vashya), 0.0)
    return {
        "name": "Vashya",
        "max": 2,
        "score": score,
        "bride": bride_vashya,
        "groom": groom_vashya,
    }


# ---------------------------------------------------------------------------
# Tara / Dina (3 points) -- birth-star compatibility, counted both ways.
# Count from one nakshatra to the other, take remainder mod 9; remainders
# 3, 5 and 7 are inauspicious. Each direction is worth 1.5.
# ---------------------------------------------------------------------------
INAUSPICIOUS_TARA = {3, 5, 7}


def _tara_ok(from_nak: int, to_nak: int) -> bool:
    count = ((to_nak - from_nak) % 27) + 1
    remainder = count % 9
    return remainder not in INAUSPICIOUS_TARA


def tara_koota(bride_nak: int, groom_nak: int) -> dict:
    from_bride = _tara_ok(bride_nak, groom_nak)
    from_groom = _tara_ok(groom_nak, bride_nak)
    score = (1.5 if from_bride else 0.0) + (1.5 if from_groom else 0.0)
    return {
        "name": "Tara",
        "max": 3,
        "score": score,
        "bride": "auspicious" if from_groom else "inauspicious",
        "groom": "auspicious" if from_bride else "inauspicious",
    }


# ---------------------------------------------------------------------------
# Yoni (4 points) -- animal-symbol sexual/temperamental compatibility.
#
# SIMPLIFICATION, DELIBERATE: the classical table grades pairs on a 5-level
# scale (same=4, friendly=3, neutral=2, enemy=1, mortal enemy=0). The
# identical case and the seven mortal-enemy pairs are unambiguous and are
# implemented exactly. The friendly/neutral/enemy gradations between the
# remaining pairs differ meaningfully between published tables, so rather
# than encode a guessed 14x14 matrix, everything else scores neutral (2).
#
# Consequence: for pairs that are neither identical nor mortal enemies,
# this can differ from AstroSage/Prokerala by 1 point in either direction.
# Fix by replacing the fallback below with a pundit-verified full matrix.
# ---------------------------------------------------------------------------
YONI_BY_NAKSHATRA = [
    "Horse",     # Ashwini
    "Elephant",  # Bharani
    "Sheep",     # Krittika
    "Serpent",   # Rohini
    "Serpent",   # Mrigashira
    "Dog",       # Ardra
    "Cat",       # Punarvasu
    "Sheep",     # Pushya
    "Cat",       # Ashlesha
    "Rat",       # Magha
    "Rat",       # Purva Phalguni
    "Cow",       # Uttara Phalguni
    "Buffalo",   # Hasta
    "Tiger",     # Chitra
    "Buffalo",   # Swati
    "Tiger",     # Vishakha
    "Deer",      # Anuradha
    "Deer",      # Jyeshtha
    "Dog",       # Mula
    "Monkey",    # Purva Ashadha
    "Mongoose",  # Uttara Ashadha
    "Monkey",    # Shravana
    "Lion",      # Dhanishta
    "Horse",     # Shatabhisha
    "Lion",      # Purva Bhadrapada
    "Cow",       # Uttara Bhadrapada
    "Elephant",  # Revati
]

YONI_MORTAL_ENEMIES = [
    {"Cow", "Tiger"},
    {"Elephant", "Lion"},
    {"Horse", "Buffalo"},
    {"Dog", "Deer"},
    {"Serpent", "Mongoose"},
    {"Cat", "Rat"},
    {"Monkey", "Sheep"},
]

YONI_NEUTRAL_FALLBACK = 2.0


def yoni_koota(bride_nak: int, groom_nak: int) -> dict:
    bride_yoni = YONI_BY_NAKSHATRA[bride_nak]
    groom_yoni = YONI_BY_NAKSHATRA[groom_nak]

    if bride_yoni == groom_yoni:
        score = 4.0
    elif {bride_yoni, groom_yoni} in YONI_MORTAL_ENEMIES:
        score = 0.0
    else:
        score = YONI_NEUTRAL_FALLBACK

    return {
        "name": "Yoni",
        "max": 4,
        "score": score,
        "bride": bride_yoni,
        "groom": groom_yoni,
    }


# ---------------------------------------------------------------------------
# Graha Maitri (5 points) -- friendship between the lords of the Moon signs.
# ---------------------------------------------------------------------------
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

PLANET_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
PLANET_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}


def _relation(of: str, toward: str) -> str:
    if of == toward:
        return "same"
    if toward in PLANET_FRIENDS[of]:
        return "friend"
    if toward in PLANET_ENEMIES[of]:
        return "enemy"
    return "neutral"


def graha_maitri_koota(bride_moon_sign: int, groom_moon_sign: int) -> dict:
    bride_lord = SIGN_LORDS[bride_moon_sign]
    groom_lord = SIGN_LORDS[groom_moon_sign]

    r1 = _relation(groom_lord, bride_lord)
    r2 = _relation(bride_lord, groom_lord)
    pair = {r1, r2}

    if "same" in pair:
        score = 5.0
    elif pair == {"friend"}:
        score = 5.0
    elif pair == {"friend", "neutral"}:
        score = 4.0
    elif pair == {"neutral"}:
        score = 3.0
    elif pair == {"friend", "enemy"}:
        score = 1.0
    elif pair == {"neutral", "enemy"}:
        score = 0.5
    else:  # both enemies
        score = 0.0

    return {
        "name": "Graha Maitri",
        "max": 5,
        "score": score,
        "bride": bride_lord,
        "groom": groom_lord,
    }


# ---------------------------------------------------------------------------
# Gana (6 points) -- temperament class. Unambiguous nakshatra assignment.
# ---------------------------------------------------------------------------
GANA_BY_NAKSHATRA = [
    "Deva",      # Ashwini
    "Manushya",  # Bharani
    "Rakshasa",  # Krittika
    "Manushya",  # Rohini
    "Deva",      # Mrigashira
    "Manushya",  # Ardra
    "Deva",      # Punarvasu
    "Deva",      # Pushya
    "Rakshasa",  # Ashlesha
    "Rakshasa",  # Magha
    "Manushya",  # Purva Phalguni
    "Manushya",  # Uttara Phalguni
    "Deva",      # Hasta
    "Rakshasa",  # Chitra
    "Deva",      # Swati
    "Rakshasa",  # Vishakha
    "Deva",      # Anuradha
    "Rakshasa",  # Jyeshtha
    "Rakshasa",  # Mula
    "Manushya",  # Purva Ashadha
    "Manushya",  # Uttara Ashadha
    "Deva",      # Shravana
    "Rakshasa",  # Dhanishta
    "Rakshasa",  # Shatabhisha
    "Manushya",  # Purva Bhadrapada
    "Manushya",  # Uttara Bhadrapada
    "Deva",      # Revati
]

# Asymmetric by design: rows are the groom's gana, columns the bride's.
GANA_MATRIX = {
    ("Deva", "Deva"): 6.0,
    ("Deva", "Manushya"): 6.0,
    ("Deva", "Rakshasa"): 0.0,
    ("Manushya", "Deva"): 5.0,
    ("Manushya", "Manushya"): 6.0,
    ("Manushya", "Rakshasa"): 0.0,
    ("Rakshasa", "Deva"): 1.0,
    ("Rakshasa", "Manushya"): 0.0,
    ("Rakshasa", "Rakshasa"): 6.0,
}


def gana_koota(bride_nak: int, groom_nak: int) -> dict:
    bride_gana = GANA_BY_NAKSHATRA[bride_nak]
    groom_gana = GANA_BY_NAKSHATRA[groom_nak]
    return {
        "name": "Gana",
        "max": 6,
        "score": GANA_MATRIX[(groom_gana, bride_gana)],
        "bride": bride_gana,
        "groom": groom_gana,
    }


# ---------------------------------------------------------------------------
# Bhakoot (7 points) -- Moon-sign axis. All-or-nothing: the 6/8, 5/9 and
# 2/12 axes score zero, everything else scores full.
# ---------------------------------------------------------------------------
BHAKOOT_BLOCKED = [{6, 8}, {5, 9}, {2, 12}]


def bhakoot_koota(bride_moon_sign: int, groom_moon_sign: int) -> dict:
    forward = ((groom_moon_sign - bride_moon_sign) % 12) + 1
    backward = ((bride_moon_sign - groom_moon_sign) % 12) + 1
    axis = {forward, backward}

    blocked = any(axis == pair for pair in BHAKOOT_BLOCKED)
    return {
        "name": "Bhakoot",
        "max": 7,
        "score": 0.0 if blocked else 7.0,
        "bride": f"{backward}",
        "groom": f"{forward}",
    }


# ---------------------------------------------------------------------------
# Nadi (8 points) -- constitutional type. Same nadi scores zero; this is
# the single heaviest koota and "Nadi dosha" is the most commonly cited
# reason a match is rejected.
# ---------------------------------------------------------------------------
NADI_BY_NAKSHATRA = [
    "Adi",    # Ashwini
    "Madhya", # Bharani
    "Antya",  # Krittika
    "Antya",  # Rohini
    "Madhya", # Mrigashira
    "Adi",    # Ardra
    "Adi",    # Punarvasu
    "Madhya", # Pushya
    "Antya",  # Ashlesha
    "Antya",  # Magha
    "Madhya", # Purva Phalguni
    "Adi",    # Uttara Phalguni
    "Adi",    # Hasta
    "Madhya", # Chitra
    "Antya",  # Swati
    "Antya",  # Vishakha
    "Madhya", # Anuradha
    "Adi",    # Jyeshtha
    "Adi",    # Mula
    "Madhya", # Purva Ashadha
    "Antya",  # Uttara Ashadha
    "Antya",  # Shravana
    "Madhya", # Dhanishta
    "Adi",    # Shatabhisha
    "Adi",    # Purva Bhadrapada
    "Madhya", # Uttara Bhadrapada
    "Antya",  # Revati
]


def nadi_koota(bride_nak: int, groom_nak: int) -> dict:
    bride_nadi = NADI_BY_NAKSHATRA[bride_nak]
    groom_nadi = NADI_BY_NAKSHATRA[groom_nak]
    return {
        "name": "Nadi",
        "max": 8,
        "score": 0.0 if bride_nadi == groom_nadi else 8.0,
        "bride": bride_nadi,
        "groom": groom_nadi,
    }


# ---------------------------------------------------------------------------
# Mangal Dosha (Manglik) -- reported alongside, never folded into the 36.
# Mars in houses 1, 2, 4, 7, 8 or 12 counted from the Ascendant. Stricter
# treatments also check from the Moon and from Venus; this checks Lagna
# and Moon, and reports them separately.
# ---------------------------------------------------------------------------
MANGAL_HOUSES = {1, 2, 4, 7, 8, 12}


def mangal_dosha(bodies: dict) -> dict:
    mars_sign = bodies["Mars"]["sign_index"]
    asc_sign = bodies["Ascendant"]["sign_index"]
    moon_sign = bodies["Moon"]["sign_index"]

    house_from_lagna = ((mars_sign - asc_sign) % 12) + 1
    house_from_moon = ((mars_sign - moon_sign) % 12) + 1

    from_lagna = house_from_lagna in MANGAL_HOUSES
    from_moon = house_from_moon in MANGAL_HOUSES

    return {
        "present": from_lagna,
        "from_lagna": from_lagna,
        "from_moon": from_moon,
        "mars_house_from_lagna": house_from_lagna,
        "mars_house_from_moon": house_from_moon,
    }


def interpret(total: float) -> str:
    if total < 18:
        return "Not recommended"
    if total < 25:
        return "Acceptable"
    if total < 32:
        return "Good"
    return "Excellent"


def ashtakoot(bride_bodies: dict, groom_bodies: dict) -> dict:
    """Full 36-point Guna Milan plus Mangal Dosha for both people."""
    bride_moon_sign = bride_bodies["Moon"]["sign_index"]
    groom_moon_sign = groom_bodies["Moon"]["sign_index"]
    bride_nak = bride_bodies["Moon"]["nakshatra_index"]
    groom_nak = groom_bodies["Moon"]["nakshatra_index"]

    kootas = [
        varna_koota(bride_moon_sign, groom_moon_sign),
        vashya_koota(bride_moon_sign, groom_moon_sign),
        tara_koota(bride_nak, groom_nak),
        yoni_koota(bride_nak, groom_nak),
        graha_maitri_koota(bride_moon_sign, groom_moon_sign),
        gana_koota(bride_nak, groom_nak),
        bhakoot_koota(bride_moon_sign, groom_moon_sign),
        nadi_koota(bride_nak, groom_nak),
    ]

    total = sum(k["score"] for k in kootas)

    return {
        "kootas": kootas,
        "total": total,
        "max_total": 36,
        "interpretation": interpret(total),
        "bride_mangal": mangal_dosha(bride_bodies),
        "groom_mangal": mangal_dosha(groom_bodies),
    }
