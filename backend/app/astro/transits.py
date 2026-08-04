"""Daily transit (Gochar) report -- the Vedic counterpart to a
"personal daily horoscope".

Deliberately NOT modelled on Western daily-horoscope tools. Those use
tropical positions, Ptolemaic aspects (square/trine/sextile by degree
orb) and quadrant houses. This module uses the Vedic apparatus that the
rest of the app already speaks: sidereal positions, whole-sign houses
counted from the natal Moon (Chandra Lagna, the standard reference for
gochar), Vedic graha drishti rather than degree-orb aspects, and Tara
Bala from the nakshatra cycle.

Everything here is exact, deterministic arithmetic on positions -- there
is no estimation as there is in the Sade Sati window search. What is
*not* exact is the interpretive text: those are conventional traditional
significations, stated generically, not personalised prediction. They
are presented as such in the UI.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Tara Bala -- the 9-fold nakshatra cycle counted from the natal Moon's star
# to the transiting Moon's star. The single most-used daily indicator in
# traditional practice, and completely unambiguous to compute.
# ---------------------------------------------------------------------------
TARAS = [
    ("Janma", "mixed", "Your own birth star. Traditionally a day for rest and care with health rather than new beginnings."),
    ("Sampat", "favourable", "The star of wealth. Considered supportive for gain, prosperity and material undertakings."),
    ("Vipat", "challenging", "The star of danger. Traditionally advises caution with risk, travel and money."),
    ("Kshema", "favourable", "The star of well-being. Considered stable and supportive for ordinary work."),
    ("Pratyari", "challenging", "The star of obstacles. Traditionally warns of resistance and opposition to effort."),
    ("Sadhaka", "favourable", "The star of accomplishment. Considered good for completing what is already begun."),
    ("Vadha", "challenging", "The star of obstruction. Traditionally regarded as the most difficult of the nine."),
    ("Mitra", "favourable", "The friendly star. Considered supportive, with help arriving from others."),
    ("Ati Mitra", "favourable", "The great friend. Traditionally the most supportive of the nine."),
]


def tara_bala(natal_moon_nak: int, transit_moon_nak: int) -> dict:
    count = ((transit_moon_nak - natal_moon_nak) % 27) + 1
    index = (count - 1) % 9
    name, quality, text = TARAS[index]
    return {
        "number": index + 1,
        "name": name,
        "quality": quality,
        "description": text,
    }


# ---------------------------------------------------------------------------
# Chandra Bala -- strength of the transiting Moon by house from the natal
# Moon. Classical grouping: 1/3/6/7/10/11 supportive, 4/8/12 difficult,
# 2/5/9 middling.
# ---------------------------------------------------------------------------
CHANDRA_BALA_QUALITY = {
    1: "mixed", 2: "mixed", 3: "favourable", 4: "challenging",
    5: "mixed", 6: "favourable", 7: "favourable", 8: "challenging",
    9: "mixed", 10: "favourable", 11: "favourable", 12: "challenging",
}

MOON_HOUSE_TEXT = {
    1: ("Janma", "The Moon returns to your birth sign. Attention turns inward and energy can run low -- traditionally a day for rest rather than launching anything."),
    2: ("Dhana", "Focus falls on family, food, speech and money. Generally steady, and favourable for domestic and financial matters."),
    3: ("Vikrama", "A courage-giving position. Favourable for initiative, short journeys, siblings and communication."),
    4: ("Sukha", "Emotions run close to the surface and home matters pull for attention. Traditionally awkward for outward-facing work."),
    5: ("Putra", "Creativity, learning, children and romance come forward. Often pleasant, though judgement can be swayed by feeling."),
    6: ("Shatru", "A strong position for effort against resistance -- competition, debts, health routines and clearing obstacles."),
    7: ("Kalatra", "Partnership and dealings with others take focus. Favourable for negotiation, travel and joint decisions."),
    8: ("Randhra", "Traditionally the most difficult placement. Sudden change and hidden matters; better for reflection than action."),
    9: ("Dharma", "Fortune, teachers, ethics and long journeys. Broadly supportive, especially for study and guidance."),
    10: ("Karma", "The house of action. Favourable for career, public dealings and anything requiring authority."),
    11: ("Labha", "Traditionally the most favourable placement. Gains, friends and the fulfilment of what you have been working toward."),
    12: ("Vyaya", "Expenditure, withdrawal, sleep and foreign matters. Traditionally difficult for gain, good for rest and letting go."),
}


def chandra_bala(natal_moon_sign: int, transit_moon_sign: int) -> dict:
    house = ((transit_moon_sign - natal_moon_sign) % 12) + 1
    bhava, text = MOON_HOUSE_TEXT[house]
    return {
        "house": house,
        "bhava": bhava,
        "quality": CHANDRA_BALA_QUALITY[house],
        "description": text,
    }


# ---------------------------------------------------------------------------
# Graha drishti -- Vedic aspects. Every graha aspects the 7th house from
# itself; Mars additionally the 4th and 8th, Jupiter the 5th and 9th,
# Saturn the 3rd and 10th. The nodes are given 5/7/9 in the traditions
# that grant them drishti at all, which is why they are listed separately
# and flagged in the UI as convention-dependent.
# ---------------------------------------------------------------------------
SPECIAL_DRISHTI = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9],
}
DEFAULT_DRISHTI = [7]

# Only the slow/structural grahas are reported. Transit Moon and Mercury
# change too fast for their aspects to say anything useful on a daily
# report, and including them buries the signal in noise.
ASPECTING_PLANETS = ["Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
ASPECTED_POINTS = ["Ascendant", "Moon", "Sun"]

ASPECT_NOTES = {
    "Jupiter": "Jupiter's aspect is traditionally protective and expansive.",
    "Saturn": "Saturn's aspect is traditionally slowing and demanding, but strengthening over time.",
    "Mars": "Mars' aspect is traditionally energising and can bring friction or haste.",
    "Rahu": "Rahu's aspect is traditionally amplifying and unsettling.",
    "Ketu": "Ketu's aspect is traditionally detaching and inward-turning.",
}


def graha_drishti(natal_bodies: dict, transit_bodies: dict) -> list[dict]:
    aspects = []
    for planet in ASPECTING_PLANETS:
        transit_sign = transit_bodies[planet]["sign_index"]
        houses = SPECIAL_DRISHTI.get(planet, DEFAULT_DRISHTI)

        for point in ASPECTED_POINTS:
            natal_sign = natal_bodies[point]["sign_index"]
            distance = ((natal_sign - transit_sign) % 12) + 1

            if distance == 1:
                relation = "conjunct"
            elif distance in houses:
                relation = f"{distance}th-house aspect on"
            else:
                continue

            aspects.append({
                "transit_planet": planet,
                "relation": relation,
                "natal_point": point,
                "transit_sign": transit_bodies[planet]["sign"],
                "natal_sign": natal_bodies[point]["sign"],
                "note": ASPECT_NOTES[planet],
            })
    return aspects


# ---------------------------------------------------------------------------
# Where each transiting graha sits relative to the natal Moon and Lagna.
# ---------------------------------------------------------------------------
REPORTED_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def planet_transits(natal_bodies: dict, transit_bodies: dict) -> list[dict]:
    natal_moon_sign = natal_bodies["Moon"]["sign_index"]
    natal_asc_sign = natal_bodies["Ascendant"]["sign_index"]

    rows = []
    for planet in REPORTED_PLANETS:
        t = transit_bodies[planet]
        rows.append({
            "planet": planet,
            "sign": t["sign"],
            "degree_in_sign": t["degree_in_sign"],
            "nakshatra": t["nakshatra"],
            "retrograde": t["retrograde"],
            "house_from_moon": ((t["sign_index"] - natal_moon_sign) % 12) + 1,
            "house_from_lagna": ((t["sign_index"] - natal_asc_sign) % 12) + 1,
        })
    return rows


def daily_report(natal_bodies: dict, transit_bodies: dict) -> dict:
    natal_moon = natal_bodies["Moon"]
    transit_moon = transit_bodies["Moon"]

    return {
        "natal_moon": {
            "sign": natal_moon["sign"],
            "nakshatra": natal_moon["nakshatra"],
        },
        "transit_moon": {
            "sign": transit_moon["sign"],
            "nakshatra": transit_moon["nakshatra"],
        },
        "tara_bala": tara_bala(natal_moon["nakshatra_index"], transit_moon["nakshatra_index"]),
        "chandra_bala": chandra_bala(natal_moon["sign_index"], transit_moon["sign_index"]),
        "planet_transits": planet_transits(natal_bodies, transit_bodies),
        "aspects": graha_drishti(natal_bodies, transit_bodies),
    }
