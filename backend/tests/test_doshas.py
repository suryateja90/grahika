from datetime import datetime, timedelta, timezone

from app.astro import doshas, ephemeris

IST = timezone(timedelta(hours=5, minutes=30))


def test_kaal_sarp_yoga_absent_when_planets_straddle_axis():
    dt = datetime(1990, 8, 26, 15, 20, tzinfo=IST)
    positions = ephemeris.compute_positions(dt, 16.9891, 81.7800)
    result = doshas.kaal_sarp_yoga(positions["bodies"])
    assert result["present"] is False


def test_kaal_sarp_yoga_present_when_all_planets_on_one_side():
    bodies = {
        "Rahu": {"longitude": 0.0},
        "Ketu": {"longitude": 180.0},
        "Sun": {"longitude": 10.0},
        "Moon": {"longitude": 40.0},
        "Mars": {"longitude": 70.0},
        "Mercury": {"longitude": 100.0},
        "Jupiter": {"longitude": 130.0},
        "Venus": {"longitude": 150.0},
        "Saturn": {"longitude": 170.0},
    }
    result = doshas.kaal_sarp_yoga(bodies)
    assert result["present"] is True
    assert result["direction"] == "Rahu to Ketu"


def test_sade_sati_status_shape():
    result = doshas.sade_sati_status(moon_sign_index=6, as_of=datetime(2026, 8, 4, tzinfo=timezone.utc))
    assert isinstance(result["in_sade_sati"], bool)
    assert "next_window_start" in result
