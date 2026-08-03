# Pundit-verified chart fixtures

Drop one JSON file per verified chart here. `test_known_charts.py` picks up
every `*.json` file automatically and checks computed output against it.

This is the single most important test suite in the project: it's the
thing that actually validates the astrology engine, as opposed to just
validating that the code runs.

## Format

```json
{
  "description": "Short note on whose chart this is / source",
  "birth_datetime": "1990-05-14T08:30:00+05:30",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "ayanamsa": "lahiri",
  "expect": {
    "positions": {
      "Moon": { "sign": "Sagittarius", "nakshatra": "Purva Ashadha" },
      "Ascendant": { "sign": "Gemini" }
    },
    "vargas": {
      "Ascendant": { "D9": { "sign": "Capricorn" } }
    },
    "vimshottari_dasha_first_lord": "Venus"
  }
}
```

Only include the fields your pundit actually checked -- the test walks
whatever keys are present in `expect` and ignores the rest. Degree-level
fields aren't compared exactly; sign/nakshatra/lord names are checked
exactly since those are what a pundit will actually verify by eye.

`_template.json` is a structural example, not a verified chart -- it's
excluded from the test run (leading underscore) and should be copied,
not read as ground truth.
