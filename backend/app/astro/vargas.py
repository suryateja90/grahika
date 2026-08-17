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


def hora_sign(longitude: float) -> dict:
    """D2. Two halves of 15 degrees. Unlike every other varga this maps onto
    only two signs: Leo (the Sun's hora) and Cancer (the Moon's). Odd signs
    give Leo then Cancer; even signs the reverse."""
    sign, offset = _sign_and_offset(longitude)
    first_half = offset < 15.0
    odd = sign % 2 == 0  # sign 0 = Aries, an odd sign in the 1-based reckoning
    leo, cancer = 4, 3
    hora = (leo if first_half else cancer) if odd else (cancer if first_half else leo)
    return {"sign": SIGN_NAMES[hora], "sign_index": hora}


def dreshkana_sign(longitude: float) -> dict:
    """D3. Thirds of 10 degrees: the sign itself, the 5th from it, the 9th."""
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 3))
    dreshkana = (sign + part * 4) % 12
    return {"sign": SIGN_NAMES[dreshkana], "sign_index": dreshkana}


def chaturthamsha_sign(longitude: float) -> dict:
    """D4. Quarters of 7.5 degrees: the sign, then the 4th, 7th and 10th."""
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 4))
    return _named((sign + part * 3) % 12)


def saptamsha_sign(longitude: float) -> dict:
    """D7. Sevenths. Odd signs count from themselves, even signs from the
    7th from themselves."""
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 7))
    start = sign if sign % 2 == 0 else (sign + 6) % 12
    return _named((start + part) % 12)


def dwadashamsha_sign(longitude: float) -> dict:
    """D12. Twelfths of 2.5 degrees, counted from the sign itself."""
    sign, offset = _sign_and_offset(longitude)
    part = int(offset // (SIGN_SPAN / 12))
    return _named((sign + part) % 12)


def _named(index: int) -> dict:
    return {"sign": SIGN_NAMES[index], "sign_index": index}


# Order matters: this is the sequence the UI offers them in.
VARGA_BUILDERS = {
    "D1": rasi_sign,
    "D2": hora_sign,
    "D3": dreshkana_sign,
    "D4": chaturthamsha_sign,
    "D7": saptamsha_sign,
    "D9": navamsa_sign,
    "D10": dasamsa_sign,
    "D12": dwadashamsha_sign,
}


def compute_vargas(bodies: dict) -> dict:
    """Given the `bodies` dict from ephemeris.compute_positions, return every
    supported divisional placement per body."""
    return {
        name: {code: build(data["longitude"]) for code, build in VARGA_BUILDERS.items()}
        for name, data in bodies.items()
    }
