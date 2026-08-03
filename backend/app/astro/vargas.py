"""Divisional (varga) chart formulas.

D1 (Rasi) is just the sign the planet occupies. D9 and D10 below follow
the standard classical division rules. These are well-established formulas,
but astrological convention has regional/lineage variation -- verify
against pundit-checked reference charts (see tests/fixtures) before
trusting output in production.
"""
from __future__ import annotations

from app.astro.ephemeris import SIGN_NAMES

SIGN_SPAN = 30.0


def _sign_and_offset(longitude: float) -> tuple[int, float]:
    longitude = longitude % 360.0
    sign = int(longitude // SIGN_SPAN)
    offset = longitude % SIGN_SPAN
    return sign, offset


def rasi_sign(longitude: float) -> dict:
    sign, offset = _sign_and_offset(longitude)
    return {"sign": SIGN_NAMES[sign], "sign_index": sign, "degree_in_sign": offset}


def navamsa_sign(longitude: float) -> dict:
    """D9. Each 30 deg sign is split into 9 parts of 3d20'.

    navamsa_sign = (sign_index * 9 + part) % 12 reproduces the classical
    rule (movable signs count from themselves, fixed from the 9th, dual
    from the 5th) in one closed formula.
    """
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 9))
    navamsa = (sign * 9 + part) % 12
    return {"sign": SIGN_NAMES[navamsa], "sign_index": navamsa}


def dasamsa_sign(longitude: float) -> dict:
    """D10. Each 30 deg sign is split into 10 parts of 3 deg.

    Odd signs count from themselves; even signs count from the 9th sign
    from themselves.
    """
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 10))
    start = sign if sign % 2 == 0 else (sign + 8) % 12
    dasamsa = (start + part) % 12
    return {"sign": SIGN_NAMES[dasamsa], "sign_index": dasamsa}


def compute_vargas(bodies: dict) -> dict:
    """Given the `bodies` dict from ephemeris.compute_positions, return D1/D9/D10 per body."""
    result = {}
    for name, data in bodies.items():
        longitude = data["longitude"]
        result[name] = {
            "D1": rasi_sign(longitude),
            "D9": navamsa_sign(longitude),
            "D10": dasamsa_sign(longitude),
        }
    return result
