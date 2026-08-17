"""Avakhada Chakra -- the summary panel every printed horoscope opens with,
plus graha drishti within the natal chart.

Almost nothing here is new astronomy. Varna, Vashya, Yoni, Gana and Nadi
are already computed for Kundli Matching and are reused directly rather
than restated, so the two features can never disagree.

NOT INCLUDED: Paya. Published methods for it differ enough that a value
here would be a guess dressed as a fact, and it is one line of a summary
table rather than something a reading turns on.
"""
from __future__ import annotations

from app.astro import ephemeris
from app.astro.dasha import DASHA_ORDER
from app.astro.matching import (
    GANA_BY_NAKSHATRA,
    NADI_BY_NAKSHATRA,
    SIGN_LORDS,
    VARNA_BY_SIGN,
    VASHYA_BY_SIGN,
    YONI_BY_NAKSHATRA,
)

# Element of each sign, in zodiac order from Aries.
TATVA_BY_SIGN = [
    "Agni", "Prithvi", "Vayu", "Jala",
    "Agni", "Prithvi", "Vayu", "Jala",
    "Agni", "Prithvi", "Vayu", "Jala",
]

# The nakshatra lords cycle in Vimshottari order, three times over 27.
NAKSHATRA_LORDS = [DASHA_ORDER[i % 9] for i in range(27)]

# Namakshar: the syllable a name is traditionally begun with, one per pada.
# 27 nakshatras x 4 padas. Widely tabulated and consistent across sources.
NAMAKSHAR = [
    ["Chu", "Che", "Cho", "La"],        # Ashwini
    ["Lee", "Lu", "Le", "Lo"],          # Bharani
    ["Aa", "Ee", "Uu", "Ay"],           # Krittika
    ["O", "Va", "Vi", "Vu"],            # Rohini
    ["Ve", "Vo", "Ka", "Kee"],          # Mrigashira
    ["Ku", "Gha", "Ing", "Chha"],       # Ardra
    ["Ke", "Ko", "Ha", "Hee"],          # Punarvasu
    ["Hu", "He", "Ho", "Da"],           # Pushya
    ["Dee", "Doo", "Day", "Do"],        # Ashlesha
    ["Ma", "Mee", "Moo", "May"],        # Magha
    ["Mo", "Ta", "Tee", "Too"],         # Purva Phalguni
    ["Tay", "To", "Pa", "Pee"],         # Uttara Phalguni
    ["Pu", "Sha", "Na", "Tha"],         # Hasta
    ["Pe", "Po", "Ra", "Ree"],          # Chitra
    ["Ru", "Re", "Ro", "Ta"],           # Swati
    ["Tee", "Too", "Tay", "To"],        # Vishakha
    ["Na", "Nee", "Noo", "Nay"],        # Anuradha
    ["No", "Ya", "Yee", "Yu"],          # Jyeshtha
    ["Ye", "Yo", "Bha", "Bhee"],        # Mula
    ["Bhu", "Dha", "Pha", "Dha"],       # Purva Ashadha
    ["Bhe", "Bho", "Ja", "Jee"],        # Uttara Ashadha
    ["Ju", "Je", "Jo", "Gha"],          # Shravana
    ["Ga", "Gee", "Gu", "Ge"],          # Dhanishta
    ["Go", "Sa", "See", "Su"],          # Shatabhisha
    ["Se", "So", "Da", "Dee"],          # Purva Bhadrapada
    ["Du", "Tha", "Jha", "Da"],         # Uttara Bhadrapada
    ["De", "Do", "Cha", "Chee"],        # Revati
]


def avakhada_chakra(bodies: dict) -> dict:
    moon = bodies["Moon"]
    sign = moon["sign_index"]
    nak = moon["nakshatra_index"]
    pada = moon["nakshatra_pada"]

    return {
        "rasi": {"index": sign, "name": ephemeris.SIGN_NAMES[sign]},
        "rasi_lord": SIGN_LORDS[sign],
        "nakshatra": {"index": nak, "name": ephemeris.NAKSHATRA_NAMES[nak]},
        "pada": pada,
        "nakshatra_lord": NAKSHATRA_LORDS[nak],
        "varna": VARNA_BY_SIGN[sign],
        "vashya": VASHYA_BY_SIGN[sign],
        "yoni": YONI_BY_NAKSHATRA[nak],
        "gana": GANA_BY_NAKSHATRA[nak],
        "nadi": NADI_BY_NAKSHATRA[nak],
        "tatva": TATVA_BY_SIGN[sign],
        "namakshar": NAMAKSHAR[nak][pada - 1],
        "lagna": {
            "index": bodies["Ascendant"]["sign_index"],
            "name": bodies["Ascendant"]["sign"],
        },
        "lagna_lord": SIGN_LORDS[bodies["Ascendant"]["sign_index"]],
    }


# --- graha drishti within the natal chart --------------------------------

SPECIAL_DRISHTI = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9],
}
DEFAULT_DRISHTI = [7]
ASPECTING = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def natal_aspects(bodies: dict) -> dict:
    """Which grahas each graha aspects, and which houses.

    Houses are whole-sign from the Ascendant, consistent with the charts
    the rest of the app draws.
    """
    asc = bodies["Ascendant"]["sign_index"]

    on_planets = []
    on_bhavas = []

    for planet in ASPECTING:
        from_sign = bodies[planet]["sign_index"]
        houses = SPECIAL_DRISHTI.get(planet, DEFAULT_DRISHTI)

        aspected_houses = sorted(((from_sign + h - 1) % 12 - asc) % 12 + 1 for h in houses)
        on_bhavas.append({
            "planet": planet,
            "houses": aspected_houses,
            "from_house": ((from_sign - asc) % 12) + 1,
        })

        targets = []
        for other in ASPECTING:
            if other == planet:
                continue
            distance = ((bodies[other]["sign_index"] - from_sign) % 12) + 1
            if distance in houses:
                targets.append({"planet": other, "distance": distance})
        if targets:
            on_planets.append({"planet": planet, "aspects": targets})

    return {"on_planets": on_planets, "on_bhavas": on_bhavas}
