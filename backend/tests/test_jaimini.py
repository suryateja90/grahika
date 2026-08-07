"""Tests for Chara Karakas and the Ishta Devata.

The Rahu reversal is the subtle one: it moves backwards, so its degree is
counted from the end of its sign. Getting that wrong quietly reshuffles
every karaka beneath it, including which planet becomes Atmakaraka.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.astro import ephemeris, jaimini, vargas

IST = timezone(timedelta(hours=5, minutes=30))


def _chart(dt=datetime(1990, 8, 26, 15, 20, tzinfo=IST), lat=16.7529, lon=81.6760):
    bodies = ephemeris.compute_positions(dt, lat, lon)["bodies"]
    return bodies, vargas.compute_vargas(bodies)


def test_karaka_names_and_deity_table_are_complete():
    assert len(jaimini.CHARA_KARAKA_NAMES) == 8
    assert set(jaimini.CHARA_KARAKA_MEANING) == set(jaimini.CHARA_KARAKA_NAMES)
    for body in jaimini.ALL_BODIES:
        assert body in jaimini.DEITY_BY_PLANET


def test_eight_karakas_ranked_strictly_descending():
    bodies, _ = _chart()
    karakas = jaimini.chara_karakas(bodies)
    assert len(karakas) == 8
    assert [k["karaka"] for k in karakas] == jaimini.CHARA_KARAKA_NAMES
    degrees = [k["degree"] for k in karakas]
    assert degrees == sorted(degrees, reverse=True)
    # Ketu is never a karaka in this scheme; every other body appears once.
    planets = [k["planet"] for k in karakas]
    assert "Ketu" not in planets
    assert len(set(planets)) == 8


def test_rahu_degree_is_measured_from_the_end_of_its_sign():
    bodies, _ = _chart()
    rahu_actual = bodies["Rahu"]["degree_in_sign"]
    entry = next(k for k in jaimini.chara_karakas(bodies) if k["planet"] == "Rahu")
    # chara_karakas rounds to 4dp, so the tolerance has to allow for that.
    assert entry["degree"] == pytest.approx(30.0 - rahu_actual, abs=5e-5)


def test_rahu_reversal_actually_changes_the_ranking():
    # A synthetic chart where forgetting the reversal would make Rahu the
    # Atmakaraka when it should rank last.
    bodies = {name: {"degree_in_sign": 10.0, "sign_index": 0} for name in jaimini.KARAKA_PLANETS}
    bodies["Sun"]["degree_in_sign"] = 28.0
    bodies["Rahu"] = {"degree_in_sign": 29.0, "sign_index": 0}  # reversed -> 1.0
    bodies["Ketu"] = {"degree_in_sign": 29.0, "sign_index": 6}

    karakas = jaimini.chara_karakas(bodies)
    assert karakas[0]["planet"] == "Sun"
    assert karakas[-1]["planet"] == "Rahu"


def test_twelfth_sign_wraps_below_aries():
    # Karakamsha in Aries (0) -> 12th is Pisces (11), not -1.
    bodies, varga = _chart()
    result = jaimini.ishta_devata(bodies, varga)
    assert 0 <= result["karakamsha_sign_index"] <= 11
    assert result["twelfth_sign_index"] == (result["karakamsha_sign_index"] + 11) % 12


def test_ishta_devata_shape_and_fallback_are_consistent():
    bodies, varga = _chart()
    result = jaimini.ishta_devata(bodies, varga)

    assert result["atmakaraka"] == result["karakas"][0]["planet"]
    assert result["indicator_planet"] in jaimini.DEITY_BY_PLANET
    assert set(result["deity"]) == {"primary", "alternate"}

    # The stated basis must match whether the 12th was actually occupied.
    if result["occupants"]:
        assert "planet in the 12th" in result["basis"]
        assert result["indicator_planet"] in result["occupants"]
    else:
        assert "lord of the 12th" in result["basis"]


def test_occupants_really_sit_in_the_twelfth_sign():
    bodies, varga = _chart()
    result = jaimini.ishta_devata(bodies, varga)
    for name in result["occupants"]:
        assert bodies[name]["sign_index"] == result["twelfth_sign_index"]


def test_runs_across_a_spread_of_births():
    for year in (1975, 1988, 1996, 2004, 2019):
        bodies, varga = _chart(datetime(year, 4, 11, 6, 45, tzinfo=IST))
        result = jaimini.ishta_devata(bodies, varga)
        assert result["indicator_planet"] in jaimini.DEITY_BY_PLANET
        assert len(result["karakas"]) == 8
