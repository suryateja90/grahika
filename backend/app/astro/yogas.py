"""Yogas and doshas -- named planetary combinations in the Rasi chart.

A warning that belongs at the top rather than buried in a footnote: yoga
lists are the least standardised thing in Jyotish. Classical texts define
several hundred, commentaries disagree about the conditions, and two
programs will happily report different counts for the same chart. A
"total yogas" number is therefore a property of whichever list a program
happens to ship, not a fact about the chart.

What this module does about that:

* Every yoga carries the exact `condition` that was tested, so a reading
  can be checked rather than taken on trust.
* `effects` reports what the classical sources claim, and is phrased as
  such. It is not a prediction.
* Only the Rasi chart is examined. Several of these yogas are also read
  in divisional charts, which would change the results.
* Cancellation rules (bhanga) are deliberately not applied. A yoga listed
  here is present by its stated geometry alone; whether it delivers
  depends on strength and dasha, which is a pundit's judgement and not a
  table lookup.

Kala Sarpa and Mangal come from `doshas` and `matching` rather than being
restated, so a chart cannot be told two different stories by two tabs.
"""
from __future__ import annotations

from app.astro import doshas as dosha_module
from app.astro.matching import SIGN_LORDS, mangal_dosha

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NODES = ["Rahu", "Ketu"]

KENDRAS = (1, 4, 7, 10)
TRIKONAS = (1, 5, 9)
DUSTHANAS = (6, 8, 12)

# Own signs and exaltation sign, for the Panch Mahapurusha test.
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
EXALTATION_SIGN = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
DEBILITATION_SIGN = {name: (sign + 6) % 12 for name, sign in EXALTATION_SIGN.items()}

MAHAPURUSHA = {
    "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
    "Venus": "Malavya", "Saturn": "Sasa",
}

# Number of distinct signs the seven grahas occupy, and the name for it.
SANKHYA = {
    1: ("Gola", "all seven grahas stand in a single sign"),
    2: ("Yuga", "the seven grahas occupy exactly two signs"),
    3: ("Shoola", "the seven grahas occupy exactly three signs"),
    4: ("Kedara", "the seven grahas occupy exactly four signs"),
    5: ("Paasa", "the seven grahas occupy exactly five signs"),
    6: ("Dama", "the seven grahas occupy exactly six signs"),
    7: ("Veena", "the seven grahas occupy exactly seven signs"),
}

# Nakshatras that straddle a rasi junction; a Moon here is Ganda Moola.
GANDA_MOOLA_NAKSHATRAS = {0, 8, 9, 17, 18, 26}


# ---------------------------------------------------------------------------
# chart helpers
# ---------------------------------------------------------------------------

def _house_of(sign: int, reference_sign: int) -> int:
    """Whole-sign house number of `sign` counted from `reference_sign`."""
    return ((sign - reference_sign) % 12) + 1


def _sign_of_house(house: int, reference_sign: int) -> int:
    return (reference_sign + house - 1) % 12


def _occupants(bodies: dict, sign: int, include_nodes: bool = True) -> list[str]:
    names = GRAHAS + NODES if include_nodes else GRAHAS
    return [n for n in names if bodies[n]["sign_index"] == sign]


def _benefics(bodies: dict) -> set[str]:
    """Jupiter and Venus always; the Moon and Mercury conditionally.

    The Moon counts as benefic while bright -- between the eighth tithi of
    the waxing fortnight and the eighth of the waning, which is an
    elongation from the Sun of 90 to 270 degrees. Mercury takes the
    character of whatever it sits with, so it is benefic only when not
    sharing a sign with a natural malefic.
    """
    benefic = {"Jupiter", "Venus"}

    elongation = (bodies["Moon"]["longitude"] - bodies["Sun"]["longitude"]) % 360.0
    if 90.0 <= elongation <= 270.0:
        benefic.add("Moon")

    hard_malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    mercury_sign = bodies["Mercury"]["sign_index"]
    if not any(bodies[m]["sign_index"] == mercury_sign for m in hard_malefics):
        benefic.add("Mercury")

    return benefic


def _malefics(bodies: dict) -> set[str]:
    return (set(GRAHAS) | set(NODES)) - _benefics(bodies)


def _yoga(name, condition, effects, category="general", chart="D1") -> dict:
    return {
        "name": name,
        "condition": condition,
        "effects": effects,
        "category": category,
        "chart": chart,
    }


# ---------------------------------------------------------------------------
# yogas
# ---------------------------------------------------------------------------

def _solar_yogas(bodies: dict) -> list[dict]:
    """Vesi, Vasi and Ubhayachari -- company for the Sun, the Moon excepted."""
    sun_sign = bodies["Sun"]["sign_index"]
    companions = [n for n in GRAHAS if n != "Sun" and n != "Moon"]

    second = [n for n in companions if bodies[n]["sign_index"] == (sun_sign + 1) % 12]
    twelfth = [n for n in companions if bodies[n]["sign_index"] == (sun_sign - 1) % 12]

    found = []
    if second:
        found.append(_yoga(
            "Vesi Yoga",
            "A graha other than the Moon stands in the 2nd house from the Sun "
            f"({', '.join(second)}).",
            "The texts assign truthfulness, an even temper and a settled livelihood.",
        ))
    if twelfth:
        found.append(_yoga(
            "Vasi Yoga",
            "A graha other than the Moon stands in the 12th house from the Sun "
            f"({', '.join(twelfth)}).",
            "The texts assign skill, generosity, learning and a good name.",
        ))
    if second and twelfth:
        found.append(_yoga(
            "Ubhayachari Yoga",
            "Grahas other than the Moon flank the Sun on both sides, in the 2nd and the 12th.",
            "Read as the strongest of the three solar yogas: standing, comfort and articulacy.",
        ))
    return found


def _lunar_yogas(bodies: dict) -> list[dict]:
    """Sunapha, Anapha, Durudhara and their absence, Kemadruma."""
    moon_sign = bodies["Moon"]["sign_index"]
    companions = [n for n in GRAHAS if n not in ("Sun", "Moon")]

    second = [n for n in companions if bodies[n]["sign_index"] == (moon_sign + 1) % 12]
    twelfth = [n for n in companions if bodies[n]["sign_index"] == (moon_sign - 1) % 12]

    found = []
    if second:
        found.append(_yoga(
            "Sunapha Yoga",
            f"A graha other than the Sun stands in the 2nd from the Moon ({', '.join(second)}).",
            "Self-earned wealth and a reputation built rather than inherited.",
        ))
    if twelfth:
        found.append(_yoga(
            "Anapha Yoga",
            f"A graha other than the Sun stands in the 12th from the Moon ({', '.join(twelfth)}).",
            "Health, an agreeable nature and freedom from want.",
        ))
    if second and twelfth:
        found.append(_yoga(
            "Durudhara Yoga",
            "The Moon is flanked by grahas other than the Sun on both sides.",
            "The texts read this as means, vehicles and dependable support.",
        ))
    if not second and not twelfth:
        found.append(_yoga(
            "Kemadruma Yoga",
            "No graha other than the Sun stands in the 2nd or the 12th from the Moon.",
            "Classically an affliction: effort meeting little support. Most commentaries "
            "cancel it if a graha occupies a kendra from the Moon or from the Ascendant.",
        ))
    return found


def _mahapurusha(bodies: dict) -> list[dict]:
    """The five great-person yogas: dignity plus a kendra."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    found = []
    for graha, name in MAHAPURUSHA.items():
        sign = bodies[graha]["sign_index"]
        house = _house_of(sign, asc_sign)
        if house not in KENDRAS:
            continue
        if sign in OWN_SIGNS[graha]:
            dignity = "its own sign"
        elif sign == EXALTATION_SIGN[graha]:
            dignity = "exaltation"
        else:
            continue
        found.append(_yoga(
            f"{name} Yoga",
            f"{graha} stands in {dignity} and in a kendra (house {house}) from the Ascendant.",
            "One of the five Panch Mahapurusha yogas -- the texts treat these as marks of "
            "distinction in the affairs the graha governs.",
            category="mahapurusha",
        ))
    return found


def _conjunction_yogas(bodies: dict) -> list[dict]:
    found = []
    moon_sign = bodies["Moon"]["sign_index"]
    jupiter_house_from_moon = _house_of(bodies["Jupiter"]["sign_index"], moon_sign)
    if jupiter_house_from_moon in KENDRAS:
        found.append(_yoga(
            "Gaja-Kesari Yoga",
            f"Jupiter stands in a kendra from the Moon (house {jupiter_house_from_moon} from it).",
            "Among the most cited yogas: intelligence, standing and lasting repute.",
        ))

    if bodies["Sun"]["sign_index"] == bodies["Mercury"]["sign_index"]:
        found.append(_yoga(
            "Budha-Aditya Yoga",
            "The Sun and Mercury occupy the same sign.",
            "Sharpness of mind and skill in work. The texts qualify it where Mercury is "
            "combust, which this check does not test for.",
        ))

    if bodies["Moon"]["sign_index"] == bodies["Mars"]["sign_index"]:
        found.append(_yoga(
            "Chandra-Mangala Yoga",
            "The Moon and Mars occupy the same sign.",
            "Enterprise and earning capacity, with a temper to match.",
        ))
    return found


def _kartari_yogas(bodies: dict) -> list[dict]:
    """What flanks the Ascendant: a benefic scissor or a malefic one."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    second = _occupants(bodies, (asc_sign + 1) % 12)
    twelfth = _occupants(bodies, (asc_sign - 1) % 12)
    if not second or not twelfth:
        return []

    benefic = _benefics(bodies)
    found = []
    if all(n in benefic for n in second) and all(n in benefic for n in twelfth):
        found.append(_yoga(
            "Shubha Kartari Yoga",
            f"Benefics flank the Ascendant on both sides -- {', '.join(twelfth)} in the 12th "
            f"and {', '.join(second)} in the 2nd.",
            "Protection: the texts read it as difficulty deflected before it arrives.",
        ))
    if all(n not in benefic for n in second) and all(n not in benefic for n in twelfth):
        found.append(_yoga(
            "Papa Kartari Yoga",
            f"Malefics flank the Ascendant on both sides -- {', '.join(twelfth)} in the 12th "
            f"and {', '.join(second)} in the 2nd.",
            "Constriction: progress described as hemmed in on either side.",
        ))
    return found


def _amala_yoga(bodies: dict) -> list[dict]:
    """Only benefics in the 10th, from the Ascendant or from the Moon."""
    benefic = _benefics(bodies)
    for label, reference in (("the Ascendant", bodies["Ascendant"]["sign_index"]),
                             ("the Moon", bodies["Moon"]["sign_index"])):
        tenth = _occupants(bodies, _sign_of_house(10, reference))
        if tenth and all(n in benefic for n in tenth):
            return [_yoga(
                "Amala Yoga",
                f"Only benefics ({', '.join(tenth)}) occupy the 10th house from {label}.",
                "Amala means spotless. The texts tie it to a reputation that stays clean.",
            )]
    return []


def _adhi_yoga(bodies: dict) -> list[dict]:
    """Benefics in the 6th, 7th and 8th from the Moon."""
    benefic = _benefics(bodies)
    moon_sign = bodies["Moon"]["sign_index"]
    houses = {6: [], 7: [], 8: []}
    for house in houses:
        houses[house] = [n for n in _occupants(bodies, _sign_of_house(house, moon_sign))
                         if n in benefic]
    if all(houses.values()):
        return [_yoga(
            "Adhi Yoga",
            "Benefics occupy the 6th, 7th and 8th houses from the Moon.",
            "Read as authority and freedom from enemies.",
        )]
    return []


def _sankhya_yoga(bodies: dict) -> list[dict]:
    """Exactly one of these applies to any chart: how spread out the grahas are."""
    signs = {bodies[n]["sign_index"] for n in GRAHAS}
    name, condition = SANKHYA[len(signs)]
    effects = {
        "Gola": "Everything concentrated in one place -- the texts read narrow means and a narrow life.",
        "Yuga": "Classically an unfavourable spread: effort scattered over too little ground.",
        "Shoola": "Sharpness, and a tendency to make enemies of the wrong people.",
        "Kedara": "Read as steadiness, and gain through cultivation and patience.",
        "Paasa": "Paasa is a noose. The texts warn of constraint, and of talking too much.",
        "Dama": "Generosity and charity; the texts treat this spread as fortunate.",
        "Veena": "The grahas evenly spread. Associated with the arts and a well-liked nature.",
    }[name]
    return [_yoga(f"{name} Yoga", condition.capitalize() + ".", effects)]


def _vipareeta_yogas(bodies: dict) -> list[dict]:
    """A dusthana lord falling into another dusthana -- harm cancelling harm."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    names = {6: "Harsha", 8: "Sarala", 12: "Vimala"}
    found = []
    for house, name in names.items():
        lord = SIGN_LORDS[_sign_of_house(house, asc_sign)]
        lord_house = _house_of(bodies[lord]["sign_index"], asc_sign)
        if lord_house in DUSTHANAS:
            found.append(_yoga(
                f"{name} Yoga",
                f"The lord of the {house}th house ({lord}) stands in the {lord_house}th, "
                "itself a dusthana.",
                "A Vipareeta Raja Yoga: the texts read gain arising out of the very difficulty "
                "the houses signify.",
                category="raja",
            ))
    return found


def _raja_yogas(bodies: dict) -> list[dict]:
    """A kendra lord sharing a sign with a trikona lord."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    kendra_lords = {SIGN_LORDS[_sign_of_house(h, asc_sign)]: h for h in KENDRAS}
    trikona_lords = {SIGN_LORDS[_sign_of_house(h, asc_sign)]: h for h in TRIKONAS}

    found = []
    seen = set()
    for k_lord, k_house in kendra_lords.items():
        for t_lord, t_house in trikona_lords.items():
            if k_lord == t_lord:
                continue
            if bodies[k_lord]["sign_index"] != bodies[t_lord]["sign_index"]:
                continue
            key = tuple(sorted((k_lord, t_lord)))
            if key in seen:
                continue
            seen.add(key)
            found.append(_yoga(
                "Raja Yoga",
                f"{k_lord}, lord of the {k_house}th (a kendra), shares a sign with "
                f"{t_lord}, lord of the {t_house}th (a trikona).",
                "The classical combination for rank and authority. Its delivery depends on the "
                "strength of both lords and on the dasha running.",
                category="raja",
            ))
    return found


def _dhana_yogas(bodies: dict) -> list[dict]:
    """Wealth lords in company with the lords of self, fortune or gain."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    wealth_houses = (2, 11)
    support_houses = (1, 5, 9)

    found = []
    seen = set()
    for w in wealth_houses:
        w_lord = SIGN_LORDS[_sign_of_house(w, asc_sign)]
        for s in support_houses:
            s_lord = SIGN_LORDS[_sign_of_house(s, asc_sign)]
            if w_lord == s_lord:
                continue
            if bodies[w_lord]["sign_index"] != bodies[s_lord]["sign_index"]:
                continue
            key = tuple(sorted((w_lord, s_lord)))
            if key in seen:
                continue
            seen.add(key)
            found.append(_yoga(
                "Dhana Yoga",
                f"{w_lord}, lord of the {w}th, shares a sign with {s_lord}, lord of the {s}th.",
                "A wealth combination: the texts read accumulation rather than windfall.",
                category="dhana",
            ))
    return found


def _saraswati_yoga(bodies: dict) -> list[dict]:
    asc_sign = bodies["Ascendant"]["sign_index"]
    allowed = set(KENDRAS) | set(TRIKONAS) | {2}
    houses = {n: _house_of(bodies[n]["sign_index"], asc_sign)
              for n in ("Jupiter", "Venus", "Mercury")}
    if all(h in allowed for h in houses.values()):
        placed = ", ".join(f"{n} in the {h}th" for n, h in houses.items())
        return [_yoga(
            "Saraswati Yoga",
            f"Jupiter, Venus and Mercury all stand in a kendra, a trikona or the 2nd ({placed}).",
            "Learning, expression and skill in the arts.",
        )]
    return []


def _parvata_yoga(bodies: dict) -> list[dict]:
    asc_sign = bodies["Ascendant"]["sign_index"]
    benefic = _benefics(bodies)
    in_kendra = [n for n in GRAHAS
                 if _house_of(bodies[n]["sign_index"], asc_sign) in KENDRAS and n in benefic]
    sixth_eighth = [n for n in GRAHAS + NODES
                    if _house_of(bodies[n]["sign_index"], asc_sign) in (6, 8)]
    if in_kendra and not sixth_eighth:
        return [_yoga(
            "Parvata Yoga",
            f"Benefics occupy kendras ({', '.join(in_kendra)}) while the 6th and 8th houses "
            "are both empty.",
            "Read as eminence and a fortunate, well-supported life.",
        )]
    return []


def _shakata_yoga(bodies: dict) -> list[dict]:
    house = _house_of(bodies["Moon"]["sign_index"], bodies["Jupiter"]["sign_index"])
    if house in DUSTHANAS:
        return [_yoga(
            "Shakata Yoga",
            f"The Moon stands in the {house}th house from Jupiter.",
            "Shakata is a cartwheel: fortune described as rising and falling in turn. "
            "Commentaries cancel it when the Moon occupies a kendra from the Ascendant.",
        )]
    return []


def _debilitation_yogas(bodies: dict) -> list[dict]:
    """Grahas in their sign of fall, reported plainly rather than as a yoga."""
    fallen = [n for n in GRAHAS if bodies[n]["sign_index"] == DEBILITATION_SIGN[n]]
    if not fallen:
        return []
    return [_yoga(
        "Neecha Graha",
        f"{', '.join(fallen)} stands in its sign of debilitation.",
        "Listed for completeness. Several cancellation rules (Neecha Bhanga) can reverse this "
        "entirely; none of them are applied here.",
    )]


YOGA_CHECKS = (
    _solar_yogas, _lunar_yogas, _mahapurusha, _conjunction_yogas, _kartari_yogas,
    _amala_yoga, _adhi_yoga, _sankhya_yoga, _vipareeta_yogas, _raja_yogas,
    _dhana_yogas, _saraswati_yoga, _parvata_yoga, _shakata_yoga, _debilitation_yogas,
)


def find_yogas(bodies: dict) -> list[dict]:
    found = []
    for check in YOGA_CHECKS:
        found.extend(check(bodies))
    return found


# ---------------------------------------------------------------------------
# doshas
# ---------------------------------------------------------------------------

def _dosha(name, present, description, reasons=None) -> dict:
    return {
        "name": name,
        "present": present,
        "description": description,
        "reasons": reasons or [],
    }


def find_doshas(bodies: dict) -> list[dict]:
    """Every dosha is reported, present or not.

    Reporting the absent ones matters as much as the present ones: a
    reader who has been told elsewhere that they are Manglik wants to see
    the check that says otherwise, not silence.
    """
    asc_sign = bodies["Ascendant"]["sign_index"]
    node_signs = {bodies["Rahu"]["sign_index"], bodies["Ketu"]["sign_index"]}
    malefic = _malefics(bodies)
    out = []

    # --- Kala Sarpa: taken from the existing implementation ---------------
    kaal = dosha_module.kaal_sarp_yoga(bodies)
    out.append(_dosha(
        "Kala Sarpa Dosha",
        kaal["present"],
        "Every one of the seven classical grahas falls on one side of the Rahu-Ketu axis."
        + (f" Here they lie {kaal['direction']}." if kaal["present"] else
           " Here at least one graha falls outside that arc, so the dosha does not form."),
    ))

    # --- Mangal: taken from the matching module --------------------------
    mangal = mangal_dosha(bodies)
    reasons = []
    if mangal["from_lagna"]:
        reasons.append(f"Mars occupies the {mangal['mars_house_from_lagna']}th house from the Ascendant.")
    if mangal["from_moon"]:
        reasons.append(f"Mars occupies the {mangal['mars_house_from_moon']}th house from the Moon.")
    out.append(_dosha(
        "Manglik (Mangal) Dosha",
        mangal["present"],
        "Mars in the 1st, 2nd, 4th, 7th, 8th or 12th house is held to strain marriage. "
        "Whether the 2nd counts, and whether to reckon from the Moon as well as the "
        "Ascendant, varies by region -- both readings are shown."
        if mangal["present"] else
        "Mars falls outside the houses that raise this dosha, reckoned from the Ascendant.",
        reasons,
    ))

    # --- Guru Chandala ----------------------------------------------------
    jupiter_sign = bodies["Jupiter"]["sign_index"]
    with_node = [n for n in NODES if bodies[n]["sign_index"] == jupiter_sign]
    out.append(_dosha(
        "Guru Chandala Dosha",
        bool(with_node),
        f"Jupiter shares a sign with {' and '.join(with_node)}. The texts read the teacher's "
        "counsel as clouded, though many commentaries treat Jupiter with Ketu as a spiritual "
        "combination rather than an affliction, and read it as a yoga where Jupiter is the "
        "stronger of the two."
        if with_node else
        "Jupiter shares a sign with neither Rahu nor Ketu, so this dosha does not form.",
    ))

    # --- Angarak ----------------------------------------------------------
    mars_sign = bodies["Mars"]["sign_index"]
    mars_node = [n for n in NODES if bodies[n]["sign_index"] == mars_sign]
    out.append(_dosha(
        "Angarak Dosha",
        bool(mars_node),
        f"Mars shares a sign with {' and '.join(mars_node)} -- heat meeting a node. The texts "
        "read impulsiveness and quarrels."
        if mars_node else
        "Mars shares a sign with neither Rahu nor Ketu.",
    ))

    # --- Grahan and Pitru -------------------------------------------------
    luminary_afflicted = []
    for luminary in ("Sun", "Moon"):
        shared = [n for n in NODES if bodies[n]["sign_index"] == bodies[luminary]["sign_index"]]
        if shared:
            luminary_afflicted.append(f"{luminary} shares a sign with {' and '.join(shared)}.")
    out.append(_dosha(
        "Grahan Dosha",
        bool(luminary_afflicted),
        "A luminary standing with a node is the eclipse pattern the name refers to."
        if luminary_afflicted else
        "Neither the Sun nor the Moon shares a sign with a node.",
        luminary_afflicted,
    ))

    pitru_reasons = list(luminary_afflicted)
    # The 9th is the house of the father and the forebears, so a luminary
    # or a node standing there counts on its own -- this is the broader of
    # the two readings in circulation, and the one reference almanacs use.
    ninth_sign = _sign_of_house(9, asc_sign)
    in_ninth = [n for n in ("Sun", "Moon", "Rahu") if bodies[n]["sign_index"] == ninth_sign]
    if in_ninth:
        pitru_reasons.append(f"{', '.join(in_ninth)} occupies the 9th house.")
    for body in ("Sun", "Moon", "Rahu", "Ketu"):
        hard = [m for m in ("Mars", "Saturn")
                if bodies[m]["sign_index"] == bodies[body]["sign_index"]]
        if hard:
            pitru_reasons.append(f"{body} shares a sign with {' and '.join(hard)}.")
    out.append(_dosha(
        "Pitru Dosha",
        bool(pitru_reasons),
        "Read as an ancestral debt, indicated when the luminaries or the 9th house are "
        "afflicted by the nodes or by Saturn and Mars. The conditions vary considerably by "
        "source; the ones that matched are listed."
        if pitru_reasons else
        "The luminaries and the 9th house are free of the afflictions that raise this dosha.",
        pitru_reasons,
    ))

    # --- Ganda Moola ------------------------------------------------------
    moon_nakshatra = bodies["Moon"]["nakshatra_index"]
    is_moola = moon_nakshatra in GANDA_MOOLA_NAKSHATRAS
    out.append(_dosha(
        "Ganda Moola Dosha",
        is_moola,
        f"The Moon occupies {bodies['Moon']['nakshatra']}, one of the six nakshatras that "
        "straddle a rasi junction. Traditionally a shanti is performed; the texts tie the "
        "affliction to the first years of life rather than the whole of it."
        if is_moola else
        f"The Moon occupies {bodies['Moon']['nakshatra']}, which is not a junction nakshatra.",
    ))

    # --- Kalathra ---------------------------------------------------------
    seventh_sign = _sign_of_house(7, asc_sign)
    seventh_lord = SIGN_LORDS[seventh_sign]
    kalathra_reasons = []
    in_seventh = [n for n in _occupants(bodies, seventh_sign) if n in malefic]
    if in_seventh:
        kalathra_reasons.append(f"{', '.join(in_seventh)} occupies the 7th house.")
    with_lord = [n for n in _occupants(bodies, bodies[seventh_lord]["sign_index"])
                 if n in malefic and n != seventh_lord]
    if with_lord:
        kalathra_reasons.append(
            f"The 7th lord {seventh_lord} shares a sign with {', '.join(with_lord)}."
        )
    with_venus = [n for n in _occupants(bodies, bodies["Venus"]["sign_index"])
                  if n in malefic and n != "Venus"]
    if with_venus:
        kalathra_reasons.append(f"Venus shares a sign with {', '.join(with_venus)}.")
    out.append(_dosha(
        "Kalathra Dosha",
        bool(kalathra_reasons),
        "Malefic pressure on the 7th house, its lord, or Venus -- the three significators of "
        "the spouse. This is an indication to weigh, not a verdict on a marriage."
        if kalathra_reasons else
        "The 7th house, its lord and Venus are all free of malefic company.",
        kalathra_reasons,
    ))

    # --- Shakata ----------------------------------------------------------
    shakata_house = _house_of(bodies["Moon"]["sign_index"], bodies["Jupiter"]["sign_index"])
    out.append(_dosha(
        "Shakata Dosha",
        shakata_house in DUSTHANAS,
        f"The Moon stands in the {shakata_house}th house from Jupiter, so fortune is described "
        "as turning like a cartwheel. Commentaries cancel it when the Moon holds a kendra from "
        "the Ascendant."
        if shakata_house in DUSTHANAS else
        f"The Moon stands in the {shakata_house}th from Jupiter, outside the 6th, 8th and 12th.",
    ))

    # --- Kemadruma --------------------------------------------------------
    moon_sign = bodies["Moon"]["sign_index"]
    neighbours = [n for n in GRAHAS if n not in ("Sun", "Moon")
                  and bodies[n]["sign_index"] in ((moon_sign + 1) % 12, (moon_sign - 1) % 12)]
    out.append(_dosha(
        "Kemadruma Dosha",
        not neighbours,
        "No graha other than the Sun flanks the Moon on either side, leaving it unsupported."
        if not neighbours else
        f"The Moon is flanked by {', '.join(neighbours)}, so the dosha does not form.",
    ))

    return out


def analyse(bodies: dict) -> dict:
    """Everything the Yogas tab shows, in one pass."""
    found = find_yogas(bodies)
    dosha_list = find_doshas(bodies)
    return {
        "yogas": found,
        "doshas": dosha_list,
        "summary": {
            "total": len(found),
            "raja": sum(1 for y in found if y["category"] == "raja"),
            "dhana": sum(1 for y in found if y["category"] == "dhana"),
            "mahapurusha": sum(1 for y in found if y["category"] == "mahapurusha"),
            "general": sum(1 for y in found if y["category"] == "general"),
            "doshas_present": sum(1 for d in dosha_list if d["present"]),
        },
    }
