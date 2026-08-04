"""Tests for the daily transit (Gochar) report.

The Tara cycle is the easiest thing here to get subtly wrong -- an
off-by-one in the count makes every day's reading shift by one tara --
so it's tested directly at its boundaries rather than only via the
endpoint.
"""
from datetime import datetime, timedelta, timezone

from app.astro import ephemeris, transits

IST = timezone(timedelta(hours=5, minutes=30))


def test_tara_tables_complete():
    assert len(transits.TARAS) == 9
    assert len(transits.MOON_HOUSE_TEXT) == 12
    assert len(transits.CHANDRA_BALA_QUALITY) == 12


def test_same_nakshatra_is_janma_tara():
    # Moon back on its own birth star -> count 1 -> Janma.
    result = transits.tara_bala(natal_moon_nak=5, transit_moon_nak=5)
    assert result["number"] == 1
    assert result["name"] == "Janma"


def test_tara_cycle_wraps_every_nine_nakshatras():
    # 9 nakshatras on gives count 10, which is Janma again.
    result = transits.tara_bala(natal_moon_nak=0, transit_moon_nak=9)
    assert result["name"] == "Janma"
    # 8 nakshatras on is the 9th tara, Ati Mitra.
    result = transits.tara_bala(natal_moon_nak=0, transit_moon_nak=8)
    assert result["number"] == 9
    assert result["name"] == "Ati Mitra"


def test_tara_covers_all_nine_across_a_full_cycle():
    seen = {transits.tara_bala(0, n)["name"] for n in range(27)}
    assert len(seen) == 9


def test_tara_wraps_backwards_across_zero():
    # Natal star near the end of the cycle, transit near the start.
    result = transits.tara_bala(natal_moon_nak=26, transit_moon_nak=0)
    assert result["name"] == "Sampat"  # count of 2


def test_chandra_bala_house_math():
    # Same sign -> 1st house (Janma).
    assert transits.chandra_bala(3, 3)["house"] == 1
    # Two signs on -> 3rd house.
    assert transits.chandra_bala(3, 5)["house"] == 3
    # Wrap backwards -> 12th house.
    assert transits.chandra_bala(0, 11)["house"] == 12


def test_eleventh_is_favourable_eighth_is_challenging():
    assert transits.CHANDRA_BALA_QUALITY[11] == "favourable"
    assert transits.CHANDRA_BALA_QUALITY[8] == "challenging"


def test_saturn_gets_three_seven_ten_drishti():
    assert transits.SPECIAL_DRISHTI["Saturn"] == [3, 7, 10]
    assert transits.SPECIAL_DRISHTI["Jupiter"] == [5, 7, 9]
    assert transits.SPECIAL_DRISHTI["Mars"] == [4, 7, 8]


def test_daily_report_on_real_charts():
    natal_dt = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    transit_dt = datetime(2026, 8, 4, 12, 0, tzinfo=IST)
    natal = ephemeris.compute_positions(natal_dt, 16.9891, 81.7800)["bodies"]
    transit = ephemeris.compute_positions(transit_dt, 16.9891, 81.7800)["bodies"]

    report = transits.daily_report(natal, transit)

    assert 1 <= report["tara_bala"]["number"] <= 9
    assert 1 <= report["chandra_bala"]["house"] <= 12
    assert len(report["planet_transits"]) == 9
    for row in report["planet_transits"]:
        assert 1 <= row["house_from_moon"] <= 12
        assert 1 <= row["house_from_lagna"] <= 12
    for aspect in report["aspects"]:
        assert aspect["transit_planet"] in transits.ASPECTING_PLANETS
        assert aspect["natal_point"] in transits.ASPECTED_POINTS
