"""Tests for the added divisional charts, antardashas and Avakhada.

The varga formulas are each a different arithmetic rule, so they are
checked at the boundaries where an off-by-one would show -- the first and
last slice of a sign, and the odd/even split where the rule flips.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.astro import avakhada, dasha, ephemeris, vargas

IST = timezone(timedelta(hours=5, minutes=30))
ARIES, TAURUS, GEMINI, CANCER, LEO = 0, 1, 2, 3, 4


def deg(sign_index: int, within: float) -> float:
    return sign_index * 30.0 + within


def test_every_body_gets_every_varga():
    bodies = ephemeris.compute_positions(
        datetime(1990, 8, 26, 15, 20, tzinfo=IST), 17.0050, 81.7805
    )["bodies"]
    result = vargas.compute_vargas(bodies)
    expected = set(vargas.VARGA_BUILDERS)
    assert len(vargas.SHODASHAVARGA) == 16, "the Shodashavarga should be all sixteen"
    assert len(expected) == 23, "and the panel shows every supported varga"
    for name, per_body in result.items():
        assert set(per_body) == expected, name
        for code, placement in per_body.items():
            assert 0 <= placement["sign_index"] <= 11, (name, code)


def test_hora_only_ever_gives_cancer_or_leo():
    # D2 maps the whole zodiac onto two signs; anything else is a bug.
    for sign in range(12):
        for within in (0.0, 7.5, 14.99, 15.0, 22.5, 29.99):
            got = vargas.hora_sign(deg(sign, within))["sign_index"]
            assert got in (CANCER, LEO), (sign, within, got)


def test_hora_flips_between_odd_and_even_signs():
    # Aries is odd: first half Leo, second half Cancer.
    assert vargas.hora_sign(deg(ARIES, 5))["sign_index"] == LEO
    assert vargas.hora_sign(deg(ARIES, 20))["sign_index"] == CANCER
    # Taurus is even: the reverse.
    assert vargas.hora_sign(deg(TAURUS, 5))["sign_index"] == CANCER
    assert vargas.hora_sign(deg(TAURUS, 20))["sign_index"] == LEO


def test_dreshkana_gives_the_sign_then_the_fifth_then_the_ninth():
    assert vargas.dreshkana_sign(deg(ARIES, 5))["sign_index"] == ARIES
    assert vargas.dreshkana_sign(deg(ARIES, 15))["sign_index"] == LEO        # 5th
    assert vargas.dreshkana_sign(deg(ARIES, 25))["sign_index"] == 8          # 9th, Sagittarius


def test_chaturthamsha_steps_by_three_signs():
    assert vargas.chaturthamsha_sign(deg(ARIES, 1))["sign_index"] == ARIES
    assert vargas.chaturthamsha_sign(deg(ARIES, 10))["sign_index"] == CANCER      # 4th
    assert vargas.chaturthamsha_sign(deg(ARIES, 17))["sign_index"] == 6           # 7th, Libra
    assert vargas.chaturthamsha_sign(deg(ARIES, 25))["sign_index"] == 9           # 10th, Capricorn


def test_saptamsha_starts_from_the_seventh_for_even_signs():
    # Odd sign counts from itself.
    assert vargas.saptamsha_sign(deg(ARIES, 1))["sign_index"] == ARIES
    # Even sign starts from the 7th from itself: Taurus -> Scorpio.
    assert vargas.saptamsha_sign(deg(TAURUS, 1))["sign_index"] == 7


def test_dwadashamsha_walks_one_sign_per_slice():
    for slice_index in range(12):
        within = slice_index * 2.5 + 1.0
        expected = (ARIES + slice_index) % 12
        assert vargas.dwadashamsha_sign(deg(ARIES, within))["sign_index"] == expected


def test_last_degree_of_a_sign_stays_in_range():
    # 29.999 must not spill into the next slice or past the table.
    for build in vargas.VARGA_BUILDERS.values():
        for sign in range(12):
            got = build(deg(sign, 29.999))
            assert 0 <= got["sign_index"] <= 11


# --- antardashas ---------------------------------------------------------

def test_antardashas_partition_their_mahadasha_exactly():
    start = datetime(2008, 12, 4, tzinfo=IST)
    subs = dasha.antardashas("Saturn", start, 19.0)
    assert len(subs) == 9
    assert subs[0]["lord"] == "Saturn"          # begins with its own lord
    assert sum(s["years"] for s in subs) == pytest.approx(19.0, abs=1e-3)
    # Contiguous: each starts where the previous ended.
    for a, b in zip(subs, subs[1:]):
        assert a["end"] == b["start"]


def test_antardashas_shrink_with_a_shortened_first_mahadasha():
    # The first mahadasha is cut by the balance at birth; its subs must follow.
    full = dasha.antardashas("Venus", datetime(2000, 1, 1, tzinfo=IST), 20.0)
    partial = dasha.antardashas("Venus", datetime(2000, 1, 1, tzinfo=IST), 5.0)
    assert sum(s["years"] for s in partial) == pytest.approx(5.0, abs=1e-3)
    assert partial[0]["years"] < full[0]["years"]


def test_next_antardasha_rolls_into_the_following_mahadasha():
    birth = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    bodies = ephemeris.compute_positions(birth, 17.0050, 81.7805)["bodies"]
    timeline = dasha.vimshottari_timeline(bodies["Moon"]["longitude"], birth)

    maha = timeline[2]
    subs = dasha.antardashas(maha["lord"], datetime.fromisoformat(maha["start"]), maha["years"])
    # Sit inside the final antardasha, where the next one is in the next maha.
    inside_last = datetime.fromisoformat(subs[-1]["start"]) + timedelta(days=1)

    result = dasha.current_periods(timeline, inside_last)
    assert result["antardasha"]["lord"] == subs[-1]["lord"]
    assert result["next_antardasha"] is not None
    assert result["next_antardasha"]["lord"] == timeline[3]["lord"]


def test_current_periods_outside_the_span_returns_nulls():
    birth = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    bodies = ephemeris.compute_positions(birth, 17.0050, 81.7805)["bodies"]
    timeline = dasha.vimshottari_timeline(bodies["Moon"]["longitude"], birth)
    before = datetime(1900, 1, 1, tzinfo=IST)
    result = dasha.current_periods(timeline, before)
    assert result["mahadasha"] is None and result["antardasha"] is None


# --- avakhada + aspects --------------------------------------------------

def test_namakshar_table_covers_every_nakshatra_and_pada():
    assert len(avakhada.NAMAKSHAR) == 27
    assert all(len(padas) == 4 for padas in avakhada.NAMAKSHAR)
    assert len(avakhada.NAKSHATRA_LORDS) == 27
    assert len(avakhada.TATVA_BY_SIGN) == 12


def test_avakhada_agrees_with_the_matching_module():
    # The two features must never disagree about the same person.
    from app.astro import matching
    bodies = ephemeris.compute_positions(
        datetime(1990, 8, 26, 15, 20, tzinfo=IST), 17.0050, 81.7805
    )["bodies"]
    chakra = avakhada.avakhada_chakra(bodies)
    moon = bodies["Moon"]
    assert chakra["gana"] == matching.GANA_BY_NAKSHATRA[moon["nakshatra_index"]]
    assert chakra["nadi"] == matching.NADI_BY_NAKSHATRA[moon["nakshatra_index"]]
    assert chakra["yoni"] == matching.YONI_BY_NAKSHATRA[moon["nakshatra_index"]]
    assert chakra["varna"] == matching.VARNA_BY_SIGN[moon["sign_index"]]


def test_natal_aspects_use_the_right_drishti_per_graha():
    bodies = ephemeris.compute_positions(
        datetime(1990, 8, 26, 15, 20, tzinfo=IST), 17.0050, 81.7805
    )["bodies"]
    result = avakhada.natal_aspects(bodies)
    assert len(result["on_bhavas"]) == 9

    for row in result["on_bhavas"]:
        assert len(row["houses"]) == len(set(row["houses"]))
        assert all(1 <= h <= 12 for h in row["houses"])
        expected = len(avakhada.SPECIAL_DRISHTI.get(row["planet"], avakhada.DEFAULT_DRISHTI))
        assert len(row["houses"]) == expected, row["planet"]

    # Every distance reported must be one the graha actually casts.
    for row in result["on_planets"]:
        allowed = avakhada.SPECIAL_DRISHTI.get(row["planet"], avakhada.DEFAULT_DRISHTI)
        for target in row["aspects"]:
            assert target["distance"] in allowed
            assert target["planet"] != row["planet"]
