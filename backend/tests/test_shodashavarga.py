"""Tests for the full Shodashavarga and the deeper dasha levels.

D30 gets the most attention because it is the only varga that does not
divide its sign evenly -- it is five unequal portions belonging to five
planets, so a boundary that drifts silently changes a placement.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.astro import dasha, ephemeris, vargas

IST = timezone(timedelta(hours=5, minutes=30))
ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO = 0, 1, 2, 3, 4, 5
LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 6, 7, 8, 9, 10, 11


def deg(sign_index: int, within: float) -> float:
    return sign_index * 30.0 + within


def test_shodashavarga_has_all_sixteen():
    expected = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
                "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
    assert list(vargas.VARGA_BUILDERS) == expected


def test_every_varga_stays_inside_the_zodiac():
    # Sweep the whole circle at a fine step; nothing may fall outside 0-11.
    for code, build in vargas.VARGA_BUILDERS.items():
        for step in range(0, 3600):
            longitude = step / 10.0
            index = build(longitude)["sign_index"]
            assert 0 <= index <= 11, (code, longitude, index)


def test_last_degree_of_every_sign_is_safe():
    # 29.9999 is where an int() division most easily overruns its table.
    for code, build in vargas.VARGA_BUILDERS.items():
        for sign in range(12):
            assert 0 <= build(deg(sign, 29.9999))["sign_index"] <= 11, code


def test_trimshamsha_boundaries_for_an_odd_sign():
    # Aries: 5 Mars, 5 Saturn, 8 Jupiter, 7 Mercury, 5 Venus.
    cases = [(0.0, ARIES), (4.9, ARIES), (5.0, AQUARIUS), (9.9, AQUARIUS),
             (10.0, SAGITTARIUS), (17.9, SAGITTARIUS), (18.0, GEMINI),
             (24.9, GEMINI), (25.0, LIBRA), (29.9, LIBRA)]
    for within, expected in cases:
        assert vargas.trimshamsha_sign(deg(ARIES, within))["sign_index"] == expected, within


def test_trimshamsha_boundaries_for_an_even_sign():
    # Taurus mirrors it: 5 Venus, 7 Mercury, 8 Jupiter, 5 Saturn, 5 Mars.
    cases = [(0.0, TAURUS), (4.9, TAURUS), (5.0, VIRGO), (11.9, VIRGO),
             (12.0, PISCES), (19.9, PISCES), (20.0, CAPRICORN),
             (24.9, CAPRICORN), (25.0, SCORPIO), (29.9, SCORPIO)]
    for within, expected in cases:
        assert vargas.trimshamsha_sign(deg(TAURUS, within))["sign_index"] == expected, within


def test_trimshamsha_never_lands_on_a_luminary_sign():
    # The five portions belong to Mars, Saturn, Jupiter, Mercury and Venus,
    # so Cancer and Leo can never appear.
    for sign in range(12):
        for within in (0.5, 6, 13, 21, 27, 29.9):
            got = vargas.trimshamsha_sign(deg(sign, within))["sign_index"]
            assert got not in (CANCER, LEO), (sign, within)


def test_d16_and_d45_share_a_starting_rule_but_differ_in_step():
    # Both start movable/fixed/dual from Aries/Leo/Sagittarius, so the very
    # first slice matches while later slices diverge.
    for sign in range(12):
        assert (vargas.shodashamsha_sign(deg(sign, 0.1))["sign_index"]
                == vargas.akshavedamsha_sign(deg(sign, 0.1))["sign_index"])
    assert (vargas.shodashamsha_sign(deg(ARIES, 20))["sign_index"]
            != vargas.akshavedamsha_sign(deg(ARIES, 20))["sign_index"])


def test_d20_uses_a_different_fixed_start_from_d16():
    # A fixed sign starts from Sagittarius in D20 but Leo in D16.
    assert vargas.vimshamsha_sign(deg(TAURUS, 0.1))["sign_index"] == SAGITTARIUS
    assert vargas.shodashamsha_sign(deg(TAURUS, 0.1))["sign_index"] == LEO


def test_d27_starts_from_the_first_sign_of_the_element():
    starts = {ARIES: ARIES, TAURUS: CANCER, GEMINI: LIBRA, CANCER: CAPRICORN}
    for sign, expected in starts.items():
        assert vargas.bhamsha_sign(deg(sign, 0.1))["sign_index"] == expected


def test_d60_advances_one_sign_every_half_degree():
    for part in range(0, 60):
        within = part * 0.5 + 0.1
        expected = (ARIES + part) % 12
        assert vargas.shashtiamsha_sign(deg(ARIES, within))["sign_index"] == expected


def test_d24_flips_between_odd_and_even_signs():
    assert vargas.chaturvimshamsha_sign(deg(ARIES, 0.1))["sign_index"] == LEO
    assert vargas.chaturvimshamsha_sign(deg(TAURUS, 0.1))["sign_index"] == CANCER


# --- deeper dasha levels -------------------------------------------------

def _timeline():
    birth = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    bodies = ephemeris.compute_positions(birth, 17.0050, 81.7805)["bodies"]
    return dasha.vimshottari_timeline(bodies["Moon"]["longitude"], birth)


def test_subdivide_partitions_its_parent_at_every_level():
    timeline = _timeline()
    period = timeline[1]
    for _ in range(3):  # antar, pratyantar, sookshma
        subs = dasha.subdivide(period)
        assert len(subs) == 9
        assert subs[0]["lord"] == period["lord"]
        # years is rounded to 4dp for display, so nine of them sum to within
        # about 1e-3 of the parent -- the timestamps are the exact record.
        assert sum(s["years"] for s in subs) == pytest.approx(period["years"], abs=1e-3)
        for a, b in zip(subs, subs[1:]):
            assert a["end"] == b["start"]
        assert subs[0]["start"] == period["start"]
        period = subs[3]


def test_dasha_chain_returns_one_entry_per_level():
    timeline = _timeline()
    chain = dasha.dasha_chain(timeline, datetime.now(IST), depth=4)
    assert [c["level"] for c in chain] == [
        "Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma"
    ]
    for link in chain:
        assert link["siblings"][link["index"]] == link["period"]


def test_dasha_chain_nests_each_level_inside_the_one_above():
    timeline = _timeline()
    chain = dasha.dasha_chain(timeline, datetime.now(IST), depth=4)
    for parent, child in zip(chain, chain[1:]):
        p, c = parent["period"], child["period"]
        assert p["start"] <= c["start"] and c["end"] <= p["end"]


def test_window_clamps_at_both_ends():
    items = [{"lord": str(i)} for i in range(9)]
    # Near the start: nothing before index 0.
    assert dasha.window(items, 0, before=5, after=9) == items
    # Near the end: nothing past the last entry.
    tail = dasha.window(items, 8, before=4, after=7)
    assert tail[-1]["lord"] == "8"
    assert len(tail) == 5
    # Middle of a longer list respects both bounds.
    longer = [{"lord": str(i)} for i in range(30)]
    mid = dasha.window(longer, 15, before=5, after=9)
    assert len(mid) == 15
    assert mid[0]["lord"] == "10" and mid[-1]["lord"] == "24"
