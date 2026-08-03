"""Compares computed charts against pundit-verified fixtures.

Add real fixtures to tests/fixtures/*.json (see fixtures/README.md).
With zero non-template fixtures present, this file still runs and passes
trivially -- it's meant to gain teeth as verified charts are added.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"
client = TestClient(app)


def _fixture_files():
    return sorted(p for p in FIXTURES_DIR.glob("*.json") if not p.name.startswith("_"))


def _assert_subset(expected, actual, path=""):
    if isinstance(expected, dict):
        for key, value in expected.items():
            assert key in actual, f"missing key '{path}{key}' in computed output"
            _assert_subset(value, actual[key], f"{path}{key}.")
    else:
        assert actual == expected, f"mismatch at '{path[:-1]}': expected {expected!r}, got {actual!r}"


def test_known_charts():
    fixture_paths = _fixture_files()
    if not fixture_paths:
        pytest.skip("no pundit-verified fixtures yet -- see tests/fixtures/README.md")

    for fixture_path in fixture_paths:
        fixture = json.loads(fixture_path.read_text())

        response = client.post("/charts/compute", json={
            "birth_datetime": fixture["birth_datetime"],
            "latitude": fixture["latitude"],
            "longitude": fixture["longitude"],
            "ayanamsa": fixture.get("ayanamsa", "lahiri"),
        })
        assert response.status_code == 200, f"{fixture_path.name}: {response.text}"
        data = response.json()

        expect = fixture["expect"]

        if "positions" in expect:
            _assert_subset(expect["positions"], data["positions"], f"{fixture_path.name}:positions.")
        if "vargas" in expect:
            _assert_subset(expect["vargas"], data["vargas"], f"{fixture_path.name}:vargas.")
        if "vimshottari_dasha_first_lord" in expect:
            assert data["vimshottari_dasha"][0]["lord"] == expect["vimshottari_dasha_first_lord"], fixture_path.name
