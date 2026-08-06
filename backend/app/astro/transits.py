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
                "distance": distance,
                "natal_point": point,
                "transit_sign": transit_bodies[planet]["sign"],
                "transit_sign_index": transit_sign,
                "natal_sign": natal_bodies[point]["sign"],
                "natal_sign_index": natal_sign,
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
            # Indices travel alongside the names so a client can render the
            # same response in another language without re-requesting.
            "sign_index": t["sign_index"],
            "degree_in_sign": t["degree_in_sign"],
            "nakshatra": t["nakshatra"],
            "nakshatra_index": t["nakshatra_index"],
            "retrograde": t["retrograde"],
            "house_from_moon": ((t["sign_index"] - natal_moon_sign) % 12) + 1,
            "house_from_lagna": ((t["sign_index"] - natal_asc_sign) % 12) + 1,
        })
    return rows


# ---------------------------------------------------------------------------
# Plain-English layer.
#
# Everything above states the tradition in its own vocabulary -- Pratyari,
# Chandra Bala, "7th-house aspect" -- which is correct but unreadable to
# anyone without background. These tables say the same thing in ordinary
# language. They translate; they do not add claims the technical reading
# doesn't already make.
# ---------------------------------------------------------------------------
TARA_PLAIN = {
    "Janma": "Your energy may run lower than usual. Better for rest and looking after yourself than for starting anything new.",
    "Sampat": "A favourable day for money and for anything you are hoping to gain from.",
    "Vipat": "Take extra care today, particularly with money, travel and risky decisions.",
    "Kshema": "A steady, comfortable day. Good for ordinary work and getting through routine tasks.",
    "Pratyari": "Expect some pushback. Things are likely to take more effort than they normally would.",
    "Sadhaka": "A good day for finishing things you have already started, rather than beginning something new.",
    "Vadha": "The hardest day in the cycle. Best to keep things simple and postpone important decisions.",
    "Mitra": "Support tends to come from other people today. A good day to ask for help.",
    "Ati Mitra": "One of the best days in the cycle. Things tend to fall your way.",
}

MOON_HOUSE_PLAIN = {
    1: "Your mood turns inward and energy can dip. Go easy on yourself.",
    2: "Attention goes to family, money and home. Good for domestic matters.",
    3: "You will feel bolder than usual. Good for starting things and for short trips.",
    4: "Feelings sit close to the surface and home pulls at your attention. Outward work feels harder.",
    5: "Good for creativity, learning, children and romance.",
    6: "A strong day for pushing through obstacles -- competition, health routines, clearing debts.",
    7: "Good for dealing with other people: partners, negotiations, travel.",
    8: "A heavy day. Better for quiet reflection than for big moves.",
    9: "Luck runs with you. Good for study, travel and advice from people older or wiser.",
    10: "A strong day for work and career, and for anything public or official.",
    11: "One of the best positions. Gains, friends, and things coming together.",
    12: "Energy drains and costs come up. Good for rest, not for chasing gain.",
}

ASPECT_PLAIN = {
    ("Mars", "Ascendant"): "Extra physical energy today, with a tendency to rush. Slow down.",
    ("Mars", "Moon"): "You may feel more restless or short-tempered than usual.",
    ("Mars", "Sun"): "Strong drive today, but watch for friction with people in authority.",
    ("Jupiter", "Ascendant"): "A protective, steadying influence over the day as a whole.",
    ("Jupiter", "Moon"): "Your mood is lifted, and judgement tends to be sound.",
    ("Jupiter", "Sun"): "Support for your confidence and your standing with others.",
    ("Saturn", "Ascendant"): "The day feels slower and heavier than usual. Patience helps.",
    ("Saturn", "Moon"): "Mood may be low or serious. Worth remembering it is not the whole picture.",
    ("Saturn", "Sun"): "Extra responsibility or pressure from above. Steady effort pays off.",
    ("Rahu", "Ascendant"): "Things feel amplified and a little unsettled.",
    ("Rahu", "Moon"): "Emotions may feel exaggerated or hard to place.",
    ("Rahu", "Sun"): "Ambition runs high today; watch for overreach.",
    ("Ketu", "Ascendant"): "You may feel withdrawn or less engaged than usual.",
    ("Ketu", "Moon"): "A detached, inward sort of mood.",
    ("Ketu", "Sun"): "Less interest than usual in recognition or being seen.",
}

QUALITY_SCORE = {"favourable": 1, "mixed": 0, "challenging": -1}

HEADLINES = {
    2: "A strong day",
    1: "A generally good day",
    0: "A mixed day",
    -1: "A demanding day",
    -2: "A difficult day",
}


def plain_summary(tara: dict, chandra: dict, aspects: list[dict]) -> dict:
    """Ordinary-language rendering of the same findings shown above.

    Split into two lists on purpose. Tara Bala and Chandra Bala are driven
    by the Moon, which changes nakshatra roughly daily and sign every ~2.3
    days -- those genuinely differ day to day. The graha drishti come from
    Mars, Saturn and the nodes, which hold the same sign for weeks or
    months, so those lines are identical every day within a long window.
    Presenting them as "today" makes the report look broken when a user
    steps through dates, and overstates what the aspects actually say.
    """
    score = QUALITY_SCORE[tara["quality"]] + QUALITY_SCORE[chandra["quality"]]

    today = [TARA_PLAIN[tara["name"]], MOON_HOUSE_PLAIN[chandra["house"]]]

    # De-duplicate: a graha can hit two of your points at once, and
    # repeating the identical sentence reads like a bug to the user.
    ongoing = []
    for aspect in aspects:
        text = ASPECT_PLAIN.get((aspect["transit_planet"], aspect["natal_point"]))
        if text and text not in ongoing:
            ongoing.append(text)

    return {"headline": HEADLINES[score], "today": today, "ongoing": ongoing}


def daily_report(natal_bodies: dict, transit_bodies: dict) -> dict:
    natal_moon = natal_bodies["Moon"]
    transit_moon = transit_bodies["Moon"]

    tara = tara_bala(natal_moon["nakshatra_index"], transit_moon["nakshatra_index"])
    chandra = chandra_bala(natal_moon["sign_index"], transit_moon["sign_index"])
    aspects = graha_drishti(natal_bodies, transit_bodies)

    return {
        "natal_moon": {
            "sign": natal_moon["sign"],
            "sign_index": natal_moon["sign_index"],
            "nakshatra": natal_moon["nakshatra"],
            "nakshatra_index": natal_moon["nakshatra_index"],
        },
        "transit_moon": {
            "sign": transit_moon["sign"],
            "sign_index": transit_moon["sign_index"],
            "nakshatra": transit_moon["nakshatra"],
            "nakshatra_index": transit_moon["nakshatra_index"],
        },
        "summary": plain_summary(tara, chandra, aspects),
        "tara_bala": tara,
        "chandra_bala": chandra,
        "planet_transits": planet_transits(natal_bodies, transit_bodies),
        "aspects": aspects,
    }
