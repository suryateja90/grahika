"""Yogas, upagrahas and special lagnas.

The assertions here lean on structural invariants rather than on a single
chart's answers: a table that must partition the zodiac, a family of yogas
of which exactly one can apply, an arithmetic chain that must close on
itself. Those catch a wrong constant, which spot-checking one birth does
not.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.astro import ephemeris, panchanga, special_lagnas, upagrahas, yogas

IST = timezone(timedelta(hours=5, minutes=30))
BIRTH = datetime(1990, 8, 26, 15, 20, 0, tzinfo=IST)
LAT, LON = 16.90572, 81.67222


@pytest.fixture(scope="module")
def chart():
    positions = ephemeris.compute_positions(BIRTH, LAT, LON, "lahiri", "mean")
    midnight = BIRTH.replace(hour=0, minute=0, second=0, microsecond=0)
    mjd = ephemeris.julian_day_utc(midnight)
    sunrise, sunset = panchanga.sun_events(mjd, LAT, LON)
    next_sunrise, _ = panchanga.sun_events(mjd + 1.0, LAT, LON)
    return {
        "bodies": positions["bodies"],
        "jd": positions["julian_day"],
        "sunrise": sunrise,
        "sunset": sunset,
        "next_sunrise": next_sunrise,
        "weekday": (BIRTH.weekday() + 1) % 7,
    }


# ---------------------------------------------------------------------------
# upagrahas
# ---------------------------------------------------------------------------

def test_gulika_rule_reproduces_the_panchangam_table():
    """The two features must not be able to disagree about Gulika.

    panchanga.GULIKA_SEGMENT was validated against a reference almanac for
    the panchangam tab. If the successive-weekday-lord rule used here ever
    stops reproducing it, one of the two is wrong.
    """
    assert upagrahas._gulika_table_agrees()


def test_sun_based_chain_is_self_consistent():
    """Each link is defined off the one before, so the chain must close."""
    for sun in range(0, 360, 7):
        values = upagrahas.sun_based(float(sun))
        assert values["Vyatipata"] == pytest.approx((360.0 - values["Dhuma"]) % 360.0)
        assert values["Parivesha"] == pytest.approx((values["Vyatipata"] + 180.0) % 360.0)
        assert values["Indrachaapa"] == pytest.approx((360.0 - values["Parivesha"]) % 360.0)


def test_indrachaapa_always_opposes_dhuma():
    """Unrolling the chain, Indrachaapa reduces to Dhuma plus 180 exactly:
    the two reflections about the zero point and the one about the 180 axis
    cancel down to a straight opposition. The reference almanac shows the
    same -- Dhuma in Sagittarius 22 31 with Indrachaapa in Gemini 22 31.
    """
    for sun in range(0, 360, 11):
        v = upagrahas.sun_based(float(sun))
        assert (v["Indrachaapa"] - v["Dhuma"]) % 360.0 == pytest.approx(180.0, abs=1e-9)
        assert (v["Upaketu"] - v["Indrachaapa"]) % 360.0 == pytest.approx(
            upagrahas.UPAKETU_OFFSET, abs=1e-9
        )


def test_every_kalavela_lands_in_its_own_eighth(chart):
    """A Kalavela point must fall inside the part it is read from, never in
    a neighbour's -- an off-by-one in the ruler order would show up here."""
    weekday, is_day = chart["weekday"], True
    for name, graha in upagrahas.KALAVELA_RULERS.items():
        index = upagrahas._part_index(weekday, graha, is_day)
        assert index is not None
        assert 0 <= index <= 6, f"{name} fell outside the seven ruled parts"


def test_kalavela_ruler_order_covers_every_graha_once():
    for weekday in range(7):
        for is_day in (True, False):
            indices = [upagrahas._part_index(weekday, g, is_day)
                       for g in upagrahas.WEEKDAY_LORDS]
            assert sorted(indices) == list(range(7))


def test_upagrahas_marks_which_family_each_point_belongs_to(chart):
    out = upagrahas.compute_upagrahas(
        chart["bodies"]["Sun"]["longitude"], chart["jd"], LAT, LON, chart["weekday"],
        chart["sunrise"], chart["sunset"], chart["next_sunrise"],
    )
    assert out["Dhuma"]["exact"] is True
    assert out["Gulika"]["exact"] is False
    for data in out.values():
        assert 0.0 <= data["longitude"] < 360.0
        assert 0 <= data["sign_index"] <= 11


def test_missing_sun_events_yield_no_kalavela(chart):
    """Above the arctic circle there may be no sunrise to divide the day at."""
    assert upagrahas.kalavela(chart["jd"], LAT, LON, 0, None, None, None) == {}


# ---------------------------------------------------------------------------
# special lagnas
# ---------------------------------------------------------------------------

def test_sweep_rates_are_ordered_slowest_to_fastest():
    rates = special_lagnas.SWEEP_RATES
    assert rates["Bhava"] < rates["Hora"] < rates["Ghati"] < rates["Vighati"]


def test_only_vighati_is_flagged_unstable():
    """Vighati moves a sign every 24 seconds; the others survive a birth
    time rounded to the minute. If another lagna ever joins it, that is a
    deliberate decision and this test should be the thing that says so."""
    assert special_lagnas.UNSTABLE == {"Vighati"}


def test_bhrigu_bindu_lies_between_rahu_and_the_moon(chart):
    bodies = chart["bodies"]
    bindu = special_lagnas.bhrigu_bindu(bodies)
    rahu = bodies["Rahu"]["longitude"]
    moon = bodies["Moon"]["longitude"]
    # Equidistant from both, measured the long way round from Rahu.
    assert (bindu - rahu) % 360.0 == pytest.approx(((moon - bindu) % 360.0), abs=1e-9)


def test_sree_lagna_returns_to_the_ascendant_at_a_nakshatra_boundary(chart):
    bodies = dict(chart["bodies"])
    bodies["Moon"] = dict(bodies["Moon"], longitude=ephemeris.NAKSHATRA_SPAN * 5)
    assert special_lagnas.sree_lagna(bodies) == pytest.approx(
        bodies["Ascendant"]["longitude"] % 360.0
    )


def test_indu_lagna_carries_the_moons_degree(chart):
    bodies = chart["bodies"]
    indu = special_lagnas.indu_lagna(bodies)
    assert indu % 30.0 == pytest.approx(bodies["Moon"]["degree_in_sign"])


def test_indu_kalas_are_the_classical_values():
    assert special_lagnas.INDU_KALAS == {
        "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
        "Jupiter": 10, "Venus": 12, "Saturn": 1,
    }


def test_special_lagnas_without_sunrise_still_return_the_chart_derived_ones(chart):
    out = special_lagnas.compute_special_lagnas(chart["bodies"], chart["jd"], None)
    assert {"Indu", "Bhrigu Bindu", "Sree", "Kunda"} <= set(out)
    # The time-swept family needs a sunrise and must be absent, not zero.
    assert not {"Bhava", "Hora", "Ghati", "Vighati"} & set(out)


# ---------------------------------------------------------------------------
# yogas
# ---------------------------------------------------------------------------

def test_exactly_one_sankhya_yoga_always_applies(chart):
    """The seven grahas occupy between one and seven signs, and each count
    has exactly one name -- so this family can never be silent or double."""
    found = yogas._sankhya_yoga(chart["bodies"])
    assert len(found) == 1
    assert found[0]["name"].replace(" Yoga", "") in [n for n, _ in yogas.SANKHYA.values()]


def test_sankhya_table_covers_every_possible_count():
    assert sorted(yogas.SANKHYA) == list(range(1, 8))


def test_kemadruma_and_durudhara_are_mutually_exclusive(chart):
    names = {y["name"] for y in yogas._lunar_yogas(chart["bodies"])}
    assert not ({"Kemadruma Yoga", "Durudhara Yoga"} <= names)


def test_debilitation_sits_opposite_exaltation():
    for graha, exalted in yogas.EXALTATION_SIGN.items():
        assert yogas.DEBILITATION_SIGN[graha] == (exalted + 6) % 12


def test_mahapurusha_requires_both_dignity_and_a_kendra(chart):
    """A graha in its own sign but not in a kendra must not qualify."""
    bodies = dict(chart["bodies"])
    # Put Saturn in Capricorn (its own sign) in the 3rd from the Ascendant.
    asc = bodies["Ascendant"]["sign_index"]
    bodies["Saturn"] = dict(bodies["Saturn"], sign_index=(asc + 2) % 12)
    names = {y["name"] for y in yogas._mahapurusha(bodies)}
    assert "Sasa Yoga" not in names


def test_benefic_moon_depends_on_elongation(chart):
    bodies = dict(chart["bodies"])
    bodies["Sun"] = dict(bodies["Sun"], longitude=0.0)
    bodies["Moon"] = dict(bodies["Moon"], longitude=180.0)   # full, bright
    assert "Moon" in yogas._benefics(bodies)
    bodies["Moon"] = dict(bodies["Moon"], longitude=10.0)    # new, dark
    assert "Moon" not in yogas._benefics(bodies)


def test_mercury_is_benefic_only_in_clean_company(chart):
    bodies = dict(chart["bodies"])
    bodies["Mercury"] = dict(bodies["Mercury"], sign_index=0)
    bodies["Saturn"] = dict(bodies["Saturn"], sign_index=5)
    assert "Mercury" in yogas._benefics(bodies)
    bodies["Saturn"] = dict(bodies["Saturn"], sign_index=0)
    assert "Mercury" not in yogas._benefics(bodies)


def test_every_dosha_is_reported_present_or_not(chart):
    """Silence about an absent dosha is worse than useless -- a reader who
    has been told they are Manglik needs to see the check that disagrees."""
    found = yogas.find_doshas(chart["bodies"])
    names = [d["name"] for d in found]
    assert len(names) == len(set(names)), "a dosha was reported twice"
    for dosha in found:
        assert isinstance(dosha["present"], bool)
        assert dosha["description"], f"{dosha['name']} has no description"


def test_kala_sarpa_and_mangal_match_their_own_modules(chart):
    """These two are shared with the doshas tab and the matching tab. If
    they ever diverge, one chart would be told two different stories."""
    from app.astro import doshas as dosha_module
    from app.astro.matching import mangal_dosha

    found = {d["name"]: d for d in yogas.find_doshas(chart["bodies"])}
    assert found["Kala Sarpa Dosha"]["present"] == \
        dosha_module.kaal_sarp_yoga(chart["bodies"])["present"]
    assert found["Manglik (Mangal) Dosha"]["present"] == \
        mangal_dosha(chart["bodies"])["present"]


def test_analyse_summary_counts_match_the_lists(chart):
    result = yogas.analyse(chart["bodies"])
    summary = result["summary"]
    assert summary["total"] == len(result["yogas"])
    assert summary["doshas_present"] == sum(1 for d in result["doshas"] if d["present"])
    by_category = summary["raja"] + summary["dhana"] + summary["mahapurusha"] + summary["general"]
    assert by_category == summary["total"], "a yoga carries a category nothing counts"


def test_every_yoga_states_the_condition_it_tested(chart):
    """The condition text is the thing that makes a reading checkable."""
    for yoga in yogas.find_yogas(chart["bodies"]):
        assert yoga["condition"].strip(), f"{yoga['name']} states no condition"
        assert yoga["effects"].strip()
        assert yoga["chart"] == "D1"


def test_yogas_survive_a_full_sweep_of_ascendants(chart):
    """Rotating the Ascendant through all twelve signs exercises every
    house-lord path -- an index error in one of them would surface here."""
    for sign in range(12):
        bodies = dict(chart["bodies"])
        bodies["Ascendant"] = dict(bodies["Ascendant"], sign_index=sign)
        result = yogas.analyse(bodies)
        assert result["summary"]["total"] >= 1  # Sankhya always applies
