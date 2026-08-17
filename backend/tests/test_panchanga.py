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

    # varjyam follows the nakshatra rather than the solar day; brahma ends at
    # sunrise and godhuli straddles sunset, so all three sit outside daylight
    # by design.
    outside_daylight = {"varjyam", "brahma", "godhuli"}

    for name, value in result["periods"].items():
        windows = value if isinstance(value, list) else [value]
        for window in windows:
            assert window["start"] is not None and window["end"] is not None
            assert window["start"] < window["end"], name
            if name not in outside_daylight:
                assert result["sunrise"] <= window["start"], name
                assert window["end"] <= result["sunset"], name


def test_brahma_ends_at_sunrise_and_godhuli_straddles_sunset():
    result = panchanga.compute_panchanga(date(2026, 8, 6), *TANUKU, IST)
    brahma, godhuli = result["periods"]["brahma"], result["periods"]["godhuli"]
    assert brahma["end"] <= result["sunrise"]
    assert godhuli["start"] < result["sunset"] < godhuli["end"]


def test_durmuhurta_matches_its_weekday_table():
    result = panchanga.compute_panchanga(date(2026, 8, 17), *TANUKU, IST)  # a Monday
    assert result["vara"]["name"] == "Monday"
    expected = len(panchanga.DURMUHURTA_BY_WEEKDAY[1])
    assert len(result["periods"]["durmuhurta"]) == expected == 2
    # Every weekday names distinct muhurtas within the fifteen.
    for weekday, muhurtas in panchanga.DURMUHURTA_BY_WEEKDAY.items():
        assert all(1 <= m <= 15 for m in muhurtas), weekday
        assert len(set(muhurtas)) == len(muhurtas), weekday


def test_day_listing_starts_before_sunrise():
    # An almanac lists the anga still running before dawn, so the first
    # entry may end earlier in the day than sunrise.
    result = panchanga.compute_panchanga(date(2026, 8, 17), *TANUKU, IST)
    for key in ("tithis", "nakshatras", "karanas", "yogas"):
        assert len(result[key]) >= 1, key
        for entry in result[key]:
            assert entry["ends_at"] is not None, key
    # The sunrise anga must be one of the entries listed for the day.
    assert result["nakshatra"]["name"] in [n["name"] for n in result["nakshatras"]]


def test_masa_and_festival_agree_with_the_tithi():
    result = panchanga.compute_panchanga(date(2026, 8, 17), *TANUKU, IST)
    assert result["masa"]["name"] == "Shravana"
    assert result["tithi"]["paksha"] == "Shukla"
    assert result["tithi"]["number"] == 5
    # Shravana Shukla Panchami is Nag Panchami.
    assert "Nag Panchami" in [f["name"] for f in result["festivals"]]


def test_moon_phase_covers_every_tithi():
    seen = {panchanga.moon_phase(i)["english"] for i in range(30)}
    assert "" not in seen
    assert "Full Moon" in seen and "New Moon" in seen


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
