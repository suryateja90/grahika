"""Tests for the daily Panchangam.

The kalam segment tables are the easiest thing here to get wrong -- a
transposed weekday shifts Rahu Kalam by hours and nobody would notice from
the code alone -- so they are checked against their classical anchors
rather than only through the API.
"""
from datetime import date, datetime

import pytz

from app.astro import panchanga

IST = pytz.timezone("Asia/Kolkata")
TANUKU = (16.7529, 81.6760)


def test_name_tables_are_the_right_length():
    assert len(panchanga.YOGA_NAMES) == 27
    assert len(panchanga.KARANA_MOVABLE) == 7
    assert len(panchanga.KARANA_FIXED) == 3
    assert len(panchanga.VARA_NAMES) == 7
    assert len(panchanga.TITHI_NAMES) == 14  # 15th is Pournami/Amavasya
    assert len(panchanga.VARJYAM_START_GHATIS) == 27


def test_tithi_naming_across_both_pakshas():
    first = panchanga.describe_tithi(0)
    assert (first["name"], first["paksha"], first["number"]) == ("Padyami", "Shukla", 1)

    full_moon = panchanga.describe_tithi(14)
    assert (full_moon["name"], full_moon["paksha"]) == ("Pournami", "Shukla")

    krishna_first = panchanga.describe_tithi(15)
    assert (krishna_first["name"], krishna_first["paksha"]) == ("Padyami", "Krishna")

    new_moon = panchanga.describe_tithi(29)
    assert (new_moon["name"], new_moon["paksha"]) == ("Amavasya", "Krishna")


def test_karana_sequence_has_one_fixed_at_the_start_and_three_at_the_end():
    assert panchanga.describe_karana(0)["name"] == "Kimstughna"
    assert panchanga.describe_karana(1)["name"] == "Bava"
    assert panchanga.describe_karana(57)["name"] == "Shakuni"
    assert panchanga.describe_karana(58)["name"] == "Chatushpada"
    assert panchanga.describe_karana(59)["name"] == "Naga"
    # The seven movable karanas cycle through the middle exactly eight times.
    middle = [panchanga.describe_karana(i)["name"] for i in range(1, 57)]
    assert len(middle) == 56
    assert all(n in panchanga.KARANA_MOVABLE for n in middle)
    assert middle.count("Vishti") == 8


def test_kalam_segment_tables_match_their_classical_anchors():
    # Seven weekdays each take a distinct eighth of the day, so the seven
    # values must be unique and inside 0..7 -- a transposed pair would
    # otherwise shift a period by hours with nothing to flag it.
    for table in (panchanga.RAHU_SEGMENT, panchanga.YAMA_SEGMENT, panchanga.GULIKA_SEGMENT):
        assert sorted(table.keys()) == list(range(7))
        assert all(0 <= v <= 7 for v in table.values())
        assert len(set(table.values())) == 7

    # Anchors every almanac agrees on, with Sunday = 0:
    assert panchanga.RAHU_SEGMENT[1] == 1      # Monday, 2nd part (07:30-09:00)
    assert panchanga.RAHU_SEGMENT[6] == 2      # Saturday, 3rd part (09:00-10:30)
    assert panchanga.YAMA_SEGMENT[4] == 0      # Thursday, 1st part
    assert panchanga.GULIKA_SEGMENT[6] == 0    # Saturday, 1st part


def test_periods_fall_inside_daylight_and_do_not_invert():
    result = panchanga.compute_panchanga(date(2026, 8, 6), *TANUKU, IST)
    assert result["sunrise"] < result["sunset"]
    for name, window in result["periods"].items():
        assert window["start"] is not None and window["end"] is not None
        if name != "varjyam":  # varjyam follows the nakshatra, not the solar day
            assert result["sunrise"] <= window["start"] < window["end"] <= result["sunset"], name


def test_abhijit_straddles_solar_noon():
    result = panchanga.compute_panchanga(date(2026, 8, 6), *TANUKU, IST)
    rise = result["sunrise"]
    setting = result["sunset"]
    midpoint = (_minutes(rise) + _minutes(setting)) / 2
    abhijit = result["periods"]["abhijit"]
    assert _minutes(abhijit["start"]) <= midpoint <= _minutes(abhijit["end"])


def test_limbs_advance_across_consecutive_days():
    # A stuck boundary search would repeat the same tithi forever.
    seen = set()
    for day in range(6, 12):
        r = panchanga.compute_panchanga(date(2026, 8, day), *TANUKU, IST)
        seen.add((r["tithi"]["name"], r["tithi"]["paksha"]))
        assert r["tithi"]["ends_at"] is not None
        assert 1 <= r["tithi"]["number"] <= 15
        assert 0 <= r["yoga"]["index"] <= 26
        assert 0 <= r["karana"]["index"] <= 59
    assert len(seen) > 1


def test_vara_matches_the_calendar():
    result = panchanga.compute_panchanga(date(2026, 8, 6), *TANUKU, IST)
    expected = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"][date(2026, 8, 6).weekday()]
    assert result["vara"]["name"] == expected


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)
