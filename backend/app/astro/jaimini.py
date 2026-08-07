"""Jaimini: Chara Karakas, Karakamsha and the Ishta Devata.

Jaimini is a distinct school from the Parashari system the rest of this
app uses. Its signatures are degree-ranked significators (the karakas)
rather than fixed ones, and sign-to-sign aspects rather than graha
drishti. Only the parts needed for the Ishta Devata are implemented here.

ON CONVENTION
Two choices below are genuinely contested and are made explicit rather
than buried:

1. Rahu is included in the karaka ranking (the eight-karaka scheme). Some
   lineages use seven and leave it out, which shifts every karaka below
   whichever position Rahu takes. Because Rahu moves backwards its
   effective degree is measured from the end of its sign.

2. The Ishta Devata is read from the 12th house from Karakamsha in the
   RASI chart. Some implementations read it in the Navamsa instead, which
   can give a different deity for the same birth.

Both are surfaced in the response so a caller can say which was used.
"""
from __future__ import annotations

from app.astro.matching import SIGN_LORDS

CHARA_KARAKA_NAMES = [
    "Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
    "Pitrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka",
]

CHARA_KARAKA_MEANING = {
    "Atmakaraka": "the soul; what this life is fundamentally about",
    "Amatyakaraka": "career and counsel; how the soul's aim is carried out",
    "Bhratrikaraka": "siblings, courage, teachers",
    "Matrikaraka": "mother, nourishment, home",
    "Pitrikaraka": "father, authority, lineage",
    "Putrakaraka": "children, creativity, past merit",
    "Gnatikaraka": "obstacles, illness, relatives who test you",
    "Darakaraka": "spouse and partnership",
}

KARAKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Primary deity, with the alternate most often given beside it. Lineages
# differ on which of a pair is named first; both are returned.
DEITY_BY_PLANET = {
    "Sun": {"primary": "Shiva", "alternate": "Rama"},
    "Moon": {"primary": "Parvati", "alternate": "Krishna"},
    "Mars": {"primary": "Subrahmanya", "alternate": "Narasimha"},
    "Mercury": {"primary": "Vishnu", "alternate": "Buddha"},
    "Jupiter": {"primary": "Dattatreya", "alternate": "Vamana"},
    "Venus": {"primary": "Lakshmi", "alternate": "Parashurama"},
    "Saturn": {"primary": "Hanuman", "alternate": "Kurma"},
    "Rahu": {"primary": "Durga", "alternate": "Varaha"},
    "Ketu": {"primary": "Ganesha", "alternate": "Matsya"},
}

ALL_BODIES = KARAKA_PLANETS + ["Rahu", "Ketu"]


def chara_karakas(bodies: dict) -> list[dict]:
    """The eight karakas, ranked by degree within sign, highest first."""
    entries = []
    for name in KARAKA_PLANETS:
        entries.append((name, bodies[name]["degree_in_sign"]))
    # Rahu is always retrograde, so its advancement through a sign is
    # counted from the far end.
    entries.append(("Rahu", 30.0 - bodies["Rahu"]["degree_in_sign"]))

    entries.sort(key=lambda pair: pair[1], reverse=True)

    return [
        {
            "karaka": CHARA_KARAKA_NAMES[i],
            "planet": planet,
            "degree": round(degree, 4),
            "meaning": CHARA_KARAKA_MEANING[CHARA_KARAKA_NAMES[i]],
        }
        for i, (planet, degree) in enumerate(entries)
    ]


def ishta_devata(bodies: dict, vargas: dict) -> dict:
    karakas = chara_karakas(bodies)
    atmakaraka = karakas[0]["planet"]

    # Karakamsha: the navamsa sign of the Atmakaraka, read as a lagna.
    karakamsha_sign = vargas[atmakaraka]["D9"]["sign_index"]
    twelfth_sign = (karakamsha_sign + 11) % 12

    occupants = [
        name for name in ALL_BODIES
        if bodies[name]["sign_index"] == twelfth_sign
    ]

    if occupants:
        # With several present the strongest by degree is taken as the
        # indicator; the rest are still reported.
        indicator = max(occupants, key=lambda n: bodies[n]["degree_in_sign"])
        basis = "planet in the 12th from Karakamsha"
    else:
        indicator = SIGN_LORDS[twelfth_sign]
        basis = "lord of the 12th from Karakamsha (no planet there)"

    return {
        "atmakaraka": atmakaraka,
        "atmakaraka_degree": karakas[0]["degree"],
        "karakamsha_sign_index": karakamsha_sign,
        "twelfth_sign_index": twelfth_sign,
        "occupants": occupants,
        "indicator_planet": indicator,
        "basis": basis,
        "deity": DEITY_BY_PLANET[indicator],
        "karakas": karakas,
        "scheme": "8-karaka (Rahu included); 12th from Karakamsha read in the Rasi chart",
    }
