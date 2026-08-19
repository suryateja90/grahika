"""Yogas and doshas -- named planetary combinations in the Rasi chart.

A warning that belongs at the top rather than buried in a footnote: yoga
lists are the least standardised thing in Jyotish. Classical texts define
several hundred, commentaries disagree about the conditions, and two
programs will happily report different counts for the same chart. A
"total yogas" number is therefore a property of whichever list a program
happens to ship, not a fact about the chart.

What this module does about that:

* Every yoga names the exact condition that was tested, so a reading can
  be checked rather than taken on trust. The wording lives in the client's
  message tables, keyed by the `key` returned here, because the sentence
  has to render in whichever language is on screen.
* The effects reported are what the classical sources claim, and are
  phrased as such. They are not predictions.
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
    "Mars": "ruchaka", "Mercury": "bhadra", "Jupiter": "hamsa",
    "Venus": "malavya", "Saturn": "sasa",
}

# Number of distinct signs the seven grahas occupy, and the yoga for it.
# Every chart lands on exactly one of these, so the family can never be
# silent and can never double up.
SANKHYA = {
    1: "gola", 2: "yuga", 3: "shoola", 4: "kedara",
    5: "paasa", 6: "dama", 7: "veena",
}

# Nakshatras that straddle a rasi junction; a Moon here is Ganda Moola.
GANDA_MOOLA_NAKSHATRAS = {0, 8, 9, 17, 18, 26}

# Afflictors for the conjunction-based dosha tests. The Sun is a natural
# malefic but deliberately excluded here, because Mercury never strays more
# than 28 degrees from it and Venus never more than 48 -- so "Venus sits
# with the Sun" or "Mercury sits with the Sun" fires in roughly half of all
# charts and carries no information. Using it as a trigger made Kalathra
# report an affliction on the same conjunction that Budha-Aditya reports as
# a benefit. Occupation of a house is a different matter and still counts
# the Sun, since that is a specific placement rather than a near-certainty.
HARD_MALEFICS = {"Mars", "Saturn", "Rahu", "Ketu"}


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



def _yoga(key, params=None, category="general", chart="D1") -> dict:
    """A yoga as a message key plus the values that go into it.

    No prose is built here, for the same reason the doshas build none: the
    sentence has to be rendered in whichever language is on screen, and one
    assembled server-side cannot be re-rendered by a language switch.
    `params` values stay raw -- graha names in English for the client to
    look up, houses as integers.
    """
    return {
        "key": key,
        "params": params or {},
        "category": category,
        "chart": chart,
    }


def _solar_yogas(bodies: dict) -> list[dict]:
    """Vesi, Vasi and Ubhayachari -- company for the Sun, the Moon excepted."""
    sun_sign = bodies["Sun"]["sign_index"]
    companions = [n for n in GRAHAS if n not in ("Sun", "Moon")]

    second = [n for n in companions if bodies[n]["sign_index"] == (sun_sign + 1) % 12]
    twelfth = [n for n in companions if bodies[n]["sign_index"] == (sun_sign - 1) % 12]

    found = []
    if second:
        found.append(_yoga("vesi", {"planets": second}))
    if twelfth:
        found.append(_yoga("vasi", {"planets": twelfth}))
    if second and twelfth:
        found.append(_yoga("ubhayachari"))
    return found


def _lunar_yogas(bodies: dict) -> list[dict]:
    """Sunapha, Anapha, Durudhara and their absence, Kemadruma."""
    moon_sign = bodies["Moon"]["sign_index"]
    companions = [n for n in GRAHAS if n not in ("Sun", "Moon")]

    second = [n for n in companions if bodies[n]["sign_index"] == (moon_sign + 1) % 12]
    twelfth = [n for n in companions if bodies[n]["sign_index"] == (moon_sign - 1) % 12]

    found = []
    if second:
        found.append(_yoga("sunapha", {"planets": second}))
    if twelfth:
        found.append(_yoga("anapha", {"planets": twelfth}))
    if second and twelfth:
        found.append(_yoga("durudhara"))
    if not second and not twelfth:
        found.append(_yoga("kemadruma"))
    return found


def _mahapurusha(bodies: dict) -> list[dict]:
    """The five great-person yogas: dignity plus a kendra."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    found = []
    for graha, key in MAHAPURUSHA.items():
        sign = bodies[graha]["sign_index"]
        house = _house_of(sign, asc_sign)
        if house not in KENDRAS:
            continue
        if sign in OWN_SIGNS[graha]:
            dignity = "own"
        elif sign == EXALTATION_SIGN[graha]:
            dignity = "exalted"
        else:
            continue
        found.append(_yoga(
            key,
            {"body": graha, "dignity": dignity, "house": house},
            category="mahapurusha",
        ))
    return found


def _conjunction_yogas(bodies: dict) -> list[dict]:
    found = []
    moon_sign = bodies["Moon"]["sign_index"]
    house = _house_of(bodies["Jupiter"]["sign_index"], moon_sign)
    if house in KENDRAS:
        found.append(_yoga("gaja_kesari", {"house": house}))

    if bodies["Sun"]["sign_index"] == bodies["Mercury"]["sign_index"]:
        found.append(_yoga("budha_aditya"))

    if bodies["Moon"]["sign_index"] == bodies["Mars"]["sign_index"]:
        found.append(_yoga("chandra_mangala"))
    return found


def _kartari_yogas(bodies: dict) -> list[dict]:
    """What flanks the Ascendant: a benefic scissor or a malefic one."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    second = _occupants(bodies, (asc_sign + 1) % 12)
    twelfth = _occupants(bodies, (asc_sign - 1) % 12)
    if not second or not twelfth:
        return []

    benefic = _benefics(bodies)
    params = {"second": second, "twelfth": twelfth}
    found = []
    if all(n in benefic for n in second) and all(n in benefic for n in twelfth):
        found.append(_yoga("shubha_kartari", params))
    if all(n not in benefic for n in second) and all(n not in benefic for n in twelfth):
        found.append(_yoga("papa_kartari", params))
    return found


def _amala_yoga(bodies: dict) -> list[dict]:
    """Only benefics in the 10th, from the Ascendant or from the Moon."""
    benefic = _benefics(bodies)
    for reference, sign in (("lagna", bodies["Ascendant"]["sign_index"]),
                            ("moon", bodies["Moon"]["sign_index"])):
        tenth = _occupants(bodies, _sign_of_house(10, sign))
        if tenth and all(n in benefic for n in tenth):
            return [_yoga("amala", {"planets": tenth, "reference": reference})]
    return []


def _adhi_yoga(bodies: dict) -> list[dict]:
    """Benefics in the 6th, 7th and 8th from the Moon."""
    benefic = _benefics(bodies)
    moon_sign = bodies["Moon"]["sign_index"]
    filled = all(
        any(n in benefic for n in _occupants(bodies, _sign_of_house(house, moon_sign)))
        for house in (6, 7, 8)
    )
    return [_yoga("adhi")] if filled else []


def _sankhya_yoga(bodies: dict) -> list[dict]:
    """Exactly one of these applies to any chart: how spread out the grahas are."""
    signs = {bodies[n]["sign_index"] for n in GRAHAS}
    return [_yoga(SANKHYA[len(signs)])]


def _vipareeta_yogas(bodies: dict) -> list[dict]:
    """A dusthana lord falling into another dusthana -- harm cancelling harm."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    keys = {6: "harsha", 8: "sarala", 12: "vimala"}
    found = []
    for house, key in keys.items():
        lord = SIGN_LORDS[_sign_of_house(house, asc_sign)]
        lord_house = _house_of(bodies[lord]["sign_index"], asc_sign)
        if lord_house in DUSTHANAS:
            found.append(_yoga(
                key,
                {"house": house, "body": lord, "lord_house": lord_house},
                category="raja",
            ))
    return found


def _raja_yogas(bodies: dict) -> list[dict]:
    """A kendra lord sharing a sign with a trikona lord."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    kendra_lords = {SIGN_LORDS[_sign_of_house(h, asc_sign)]: h for h in KENDRAS}
    trikona_lords = {SIGN_LORDS[_sign_of_house(h, asc_sign)]: h for h in TRIKONAS}

    found, seen = [], set()
    for k_lord, k_house in kendra_lords.items():
        for t_lord, t_house in trikona_lords.items():
            if k_lord == t_lord:
                continue
            if bodies[k_lord]["sign_index"] != bodies[t_lord]["sign_index"]:
                continue
            pair = tuple(sorted((k_lord, t_lord)))
            if pair in seen:
                continue
            seen.add(pair)
            found.append(_yoga(
                "raja",
                {"kendra_lord": k_lord, "kendra_house": k_house,
                 "trikona_lord": t_lord, "trikona_house": t_house},
                category="raja",
            ))
    return found


def _dhana_yogas(bodies: dict) -> list[dict]:
    """Wealth lords in company with the lords of self, fortune or gain."""
    asc_sign = bodies["Ascendant"]["sign_index"]
    found, seen = [], set()
    for w in (2, 11):
        w_lord = SIGN_LORDS[_sign_of_house(w, asc_sign)]
        for sup in (1, 5, 9):
            s_lord = SIGN_LORDS[_sign_of_house(sup, asc_sign)]
            if w_lord == s_lord:
                continue
            if bodies[w_lord]["sign_index"] != bodies[s_lord]["sign_index"]:
                continue
            pair = tuple(sorted((w_lord, s_lord)))
            if pair in seen:
                continue
            seen.add(pair)
            found.append(_yoga(
                "dhana",
                {"wealth_lord": w_lord, "wealth_house": w,
                 "support_lord": s_lord, "support_house": sup},
                category="dhana",
            ))
    return found


def _saraswati_yoga(bodies: dict) -> list[dict]:
    asc_sign = bodies["Ascendant"]["sign_index"]
    allowed = set(KENDRAS) | set(TRIKONAS) | {2}
    houses = {n: _house_of(bodies[n]["sign_index"], asc_sign)
              for n in ("Jupiter", "Venus", "Mercury")}
    if all(h in allowed for h in houses.values()):
        return [_yoga("saraswati", {
            "jupiter_house": houses["Jupiter"],
            "venus_house": houses["Venus"],
            "mercury_house": houses["Mercury"],
        })]
    return []


def _parvata_yoga(bodies: dict) -> list[dict]:
    asc_sign = bodies["Ascendant"]["sign_index"]
    benefic = _benefics(bodies)
    in_kendra = [n for n in GRAHAS
                 if _house_of(bodies[n]["sign_index"], asc_sign) in KENDRAS and n in benefic]
    sixth_eighth = [n for n in GRAHAS + NODES
                    if _house_of(bodies[n]["sign_index"], asc_sign) in (6, 8)]
    if in_kendra and not sixth_eighth:
        return [_yoga("parvata", {"planets": in_kendra})]
    return []


def _shakata_yoga(bodies: dict) -> list[dict]:
    house = _house_of(bodies["Moon"]["sign_index"], bodies["Jupiter"]["sign_index"])
    return [_yoga("shakata", {"house": house})] if house in DUSTHANAS else []


def _debilitation_yogas(bodies: dict) -> list[dict]:
    """Grahas in their sign of fall, reported plainly rather than as a yoga."""
    fallen = [n for n in GRAHAS if bodies[n]["sign_index"] == DEBILITATION_SIGN[n]]
    return [_yoga("neecha_graha", {"planets": fallen})] if fallen else []


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
# No prose is built here. Each dosha returns a message *key* and the values
# that go into it, and the client renders the sentence in whichever language
# is on screen -- the same arrangement the rest of the API uses for signs and
# nakshatras. Building the sentence server-side would have meant a round trip
# on every language switch, and would have left the Telugu page reading half
# in English, which is what it did before this.
#
# `params` values stay in their raw form: graha names in English for the
# client to look up, house numbers as integers, nakshatras as indices.


def _dosha(key, present, params=None, reasons=None) -> dict:
    return {
        "key": key,
        "present": present,
        "params": params or {},
        # Each reason is itself a key plus params, for the same reason.
        "reasons": reasons or [],
    }


def _reason(key, **params) -> dict:
    return {"key": key, "params": params}


def find_doshas(bodies: dict) -> list[dict]:
    """Every dosha is reported, present or not.

    Reporting the absent ones matters as much as the present ones: a
    reader who has been told elsewhere that they are Manglik wants to see
    the check that says otherwise, not silence.
    """
    asc_sign = bodies["Ascendant"]["sign_index"]
    out = []

    # --- Kala Sarpa: taken from the existing implementation ---------------
    kaal = dosha_module.kaal_sarp_yoga(bodies)
    out.append(_dosha(
        "kala_sarpa",
        kaal["present"],
        {"direction": "rahu_ketu" if kaal.get("direction") == "Rahu to Ketu" else "ketu_rahu"},
    ))

    # --- Mangal: taken from the matching module --------------------------
    mangal = mangal_dosha(bodies)
    reasons = []
    if mangal["from_lagna"]:
        reasons.append(_reason("mars_house_lagna", house=mangal["mars_house_from_lagna"]))
    if mangal["from_moon"]:
        reasons.append(_reason("mars_house_moon", house=mangal["mars_house_from_moon"]))
    out.append(_dosha("manglik", mangal["present"], reasons=reasons))

    # --- Guru Chandala ----------------------------------------------------
    jupiter_sign = bodies["Jupiter"]["sign_index"]
    with_node = [n for n in NODES if bodies[n]["sign_index"] == jupiter_sign]
    out.append(_dosha("guru_chandala", bool(with_node), {"planets": with_node}))

    # --- Angarak ----------------------------------------------------------
    mars_node = [n for n in NODES if bodies[n]["sign_index"] == bodies["Mars"]["sign_index"]]
    out.append(_dosha("angarak", bool(mars_node), {"planets": mars_node}))

    # --- Grahan and Pitru -------------------------------------------------
    luminary_reasons = []
    for luminary in ("Sun", "Moon"):
        shared = [n for n in NODES if bodies[n]["sign_index"] == bodies[luminary]["sign_index"]]
        if shared:
            luminary_reasons.append(
                _reason("body_with_planets", body=luminary, planets=shared)
            )
    out.append(_dosha("grahan", bool(luminary_reasons), reasons=luminary_reasons))

    pitru_reasons = list(luminary_reasons)
    # The 9th is the house of the father and the forebears, so a luminary
    # or a node standing there counts on its own -- this is the broader of
    # the two readings in circulation, and the one reference almanacs use.
    ninth_sign = _sign_of_house(9, asc_sign)
    in_ninth = [n for n in ("Sun", "Moon", "Rahu") if bodies[n]["sign_index"] == ninth_sign]
    if in_ninth:
        pitru_reasons.append(_reason("in_ninth_house", planets=in_ninth))
    for body in ("Sun", "Moon", "Rahu", "Ketu"):
        hard = [m for m in ("Mars", "Saturn")
                if bodies[m]["sign_index"] == bodies[body]["sign_index"]]
        if hard:
            pitru_reasons.append(_reason("body_with_planets", body=body, planets=hard))
    out.append(_dosha("pitru", bool(pitru_reasons), reasons=pitru_reasons))

    # --- Ganda Moola ------------------------------------------------------
    moon_nakshatra = bodies["Moon"]["nakshatra_index"]
    out.append(_dosha(
        "ganda_moola",
        moon_nakshatra in GANDA_MOOLA_NAKSHATRAS,
        {"nakshatra_index": moon_nakshatra},
    ))

    # --- Kalathra ---------------------------------------------------------
    # Kalathra means the spouse, and the dosha is named for the 7th house.
    # The house and its lord are therefore what raise it; Venus is the
    # karaka and corroborates, but an afflicted Venus alone is not enough.
    # That split matters -- Venus never strays more than 48 degrees from the
    # Sun and shares a sign with a node often, so treating it as a trigger
    # in its own right made this the most-reported dosha in the list.
    seventh_sign = _sign_of_house(7, asc_sign)
    seventh_lord = SIGN_LORDS[seventh_sign]
    primary, corroborating = [], []

    # Occupation of the 7th counts the Sun; the conjunction tests below do
    # not. See HARD_MALEFICS for why.
    in_seventh = [n for n in _occupants(bodies, seventh_sign)
                  if n in HARD_MALEFICS or n == "Sun"]
    if in_seventh:
        primary.append(_reason("malefic_in_seventh", planets=in_seventh))

    with_lord = [n for n in _occupants(bodies, bodies[seventh_lord]["sign_index"])
                 if n in HARD_MALEFICS and n != seventh_lord]
    if with_lord:
        primary.append(_reason("seventh_lord_with", body=seventh_lord, planets=with_lord))

    with_venus = [n for n in _occupants(bodies, bodies["Venus"]["sign_index"])
                  if n in HARD_MALEFICS and n != "Venus"]
    if with_venus:
        corroborating.append(_reason("body_with_planets", body="Venus", planets=with_venus))

    if primary:
        out.append(_dosha("kalathra", True, reasons=primary + corroborating))
    elif corroborating:
        # Reporting "all three are clear" here would be false -- Venus is
        # not. A distinct message says what was found and why it falls short
        # of raising the dosha.
        out.append(_dosha(
            "kalathra", False,
            {"variant": "kalathra_venus_only", "planets": with_venus},
        ))
    else:
        out.append(_dosha("kalathra", False))

    # Shakata and Kemadruma are deliberately absent from this list. Both are
    # classically Chandra *yogas* and are already reported as such above;
    # listing them here too counted one finding twice and inflated the
    # "doshas present" total. test_no_finding_is_reported_as_both guards it.

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
