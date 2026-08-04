"""Tests for Ashtakoot matching.

Table-integrity tests matter as much as scoring tests here: a typo in one
of the 27-entry nakshatra tables would silently skew every match. The
gana/nadi/yoni tables all have known correct group sizes, so those are
asserted directly.
"""
from datetime import datetime, timedelta, timezone

from app.astro import ephemeris, matching

IST = timezone(timedelta(hours=5, minutes=30))


def test_nakshatra_tables_are_27_long():
    assert len(matching.YONI_BY_NAKSHATRA) == 27
    assert len(matching.GANA_BY_NAKSHATRA) == 27
    assert len(matching.NADI_BY_NAKSHATRA) == 27


def test_sign_tables_are_12_long():
    assert len(matching.VARNA_BY_SIGN) == 12
    assert len(matching.VASHYA_BY_SIGN) == 12
    assert len(matching.SIGN_LORDS) == 12


def test_nadi_groups_are_nine_each():
    # The 27 nakshatras split exactly evenly across the three nadis.
    for nadi in ("Adi", "Madhya", "Antya"):
        assert matching.NADI_BY_NAKSHATRA.count(nadi) == 9


def test_gana_groups_are_nine_each():
    for gana in ("Deva", "Manushya", "Rakshasa"):
        assert matching.GANA_BY_NAKSHATRA.count(gana) == 9


def test_yoni_animals_pair_up():
    # 27 nakshatras over 14 animals: 13 animals appear twice, one appears once.
    counts = {}
    for animal in matching.YONI_BY_NAKSHATRA:
        counts[animal] = counts.get(animal, 0) + 1
    assert len(counts) == 14
    assert sorted(counts.values()) == [1] + [2] * 13


def test_nadi_same_scores_zero_different_scores_eight():
    # Ashwini (Adi) with Ardra (Adi) -> same nadi -> 0
    assert matching.nadi_koota(0, 5)["score"] == 0.0
    # Ashwini (Adi) with Bharani (Madhya) -> different -> 8
    assert matching.nadi_koota(0, 1)["score"] == 8.0


def test_bhakoot_blocks_six_eight_axis():
    # Aries (0) and Virgo (5): 6th/8th axis -> blocked
    assert matching.bhakoot_koota(0, 5)["score"] == 0.0
    # Aries (0) and Aries (0): same sign -> full marks
    assert matching.bhakoot_koota(0, 0)["score"] == 7.0


def test_yoni_identical_and_mortal_enemy():
    # Ashwini and Shatabhisha are both Horse -> identical -> 4
    assert matching.yoni_koota(0, 23)["score"] == 4.0
    # Uttara Phalguni (Cow) vs Chitra (Tiger) -> mortal enemies -> 0
    assert matching.yoni_koota(11, 13)["score"] == 0.0


def test_varna_awards_point_when_groom_not_lower():
    # Bride Gemini (Shudra, rank 1), groom Cancer (Brahmin, rank 4) -> 1
    assert matching.varna_koota(2, 3)["score"] == 1.0
    # Bride Cancer (Brahmin), groom Gemini (Shudra) -> 0
    assert matching.varna_koota(3, 2)["score"] == 0.0


def test_total_never_exceeds_max():
    # Sweep every sign/nakshatra combination and assert the invariant holds.
    for bride_sign in range(12):
        for groom_sign in range(12):
            bride = _fake_moon(bride_sign, bride_sign)
            groom = _fake_moon(groom_sign, groom_sign)
            result = matching.ashtakoot(bride, groom)
            assert 0.0 <= result["total"] <= 36.0
            for koota in result["kootas"]:
                assert 0.0 <= koota["score"] <= koota["max"]


def test_ashtakoot_on_real_charts():
    bride_dt = datetime(1992, 3, 14, 9, 15, tzinfo=IST)
    groom_dt = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    bride = ephemeris.compute_positions(bride_dt, 13.0836, 80.2701)["bodies"]
    groom = ephemeris.compute_positions(groom_dt, 16.9891, 81.7800)["bodies"]

    result = matching.ashtakoot(bride, groom)
    assert len(result["kootas"]) == 8
    assert result["total"] == sum(k["score"] for k in result["kootas"])
    assert result["interpretation"] in {"Not recommended", "Acceptable", "Good", "Excellent"}
    assert isinstance(result["bride_mangal"]["present"], bool)


def _fake_moon(sign_index: int, nak_seed: int) -> dict:
    return {
        "Moon": {"sign_index": sign_index, "nakshatra_index": nak_seed % 27},
        "Mars": {"sign_index": (sign_index + 3) % 12},
        "Ascendant": {"sign_index": sign_index},
    }
