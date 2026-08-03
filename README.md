# Grahika (working name)

Vedic astrology app. Pivoted from OneLync after low conversion there;
building for a niche audience (astrology) with real willingness to pay,
with pundit-verified accuracy as the core product bet.

## Stack (all free tier)

- **Backend**: FastAPI + SQLAlchemy (Python) -- same pattern as OneLync's backend
- **Astrology engine**: `pyswisseph` (Swiss Ephemeris Python binding), Moshier mode
  (`SEFLG_MOSEPH`) -- no ephemeris data files to download/host, accurate to
  ~1 arcsecond, more than sufficient for horoscope astrology
- **DB**: SQLite locally, swap to a free-tier Postgres (Neon/Supabase) in production
- **Frontend**: plain HTML/CSS/JS, no framework/build step, served by the same
  FastAPI app via `StaticFiles` -- one free Render service for everything,
  no separate Vercel deploy needed
- **Hosting**: Render free web service (`render.yaml`), API + UI together

No paid services required to build or run this. The one licensing thing to
know: Swiss Ephemeris is AGPL or commercially licensed. AGPL is fine (free)
as long as you're comfortable making this service's source available to
users if/when it's live over the network -- revisit before a closed-source
commercial launch if that matters to you.

## What's built

- `backend/app/astro/ephemeris.py` -- sidereal planetary positions (7 classical
  planets + Rahu/Ketu + Ascendant), selectable ayanamsa (Lahiri default, also
  Raman/KP/True Chitra), mean or true node
- `backend/app/astro/vargas.py` -- D1 (Rasi), D9 (Navamsa), D10 (Dasamsa)
- `backend/app/astro/dasha.py` -- Vimshottari Mahadasha timeline (120-year cycle,
  balance-of-dasha at birth handled)
- `POST /charts/compute` -- one endpoint, takes birth datetime (must include UTC
  offset) + lat/lon, returns positions + vargas + dasha timeline
- `tests/test_known_charts.py` -- fixture-based accuracy tests. **This is the
  most important part of the repo.** See `backend/tests/fixtures/README.md`.
- `frontend/` -- birth details form, North Indian-style D1/D9 diamond charts
  (SVG, generated client-side from the API response), positions table,
  mahadasha timeline table. No build tooling; open http://localhost:8000/
  once the backend is running.
- `backend/app/geocode.py` + `GET /geocode/search` -- place name -> lat/lon via
  Nominatim (OpenStreetMap, free, no API key). The frontend uses this so
  nobody needs to know or enter raw coordinates.
- Automatic historical timezone resolution: if `birth_datetime` is sent
  without a UTC offset, the backend looks up the place's IANA timezone
  (`timezonefinder`) and localizes using `pytz`'s historical rules -- e.g.
  a 1850 Chennai birth correctly resolves to +05:53 (pre-1906 Madras time),
  not a naive +05:30. This directly avoids the #1 source of wrong charts.
  An explicit "Override UTC offset" field is still available for cases
  where a pundit gives you a specific offset to reproduce.

## What's not built yet

- User accounts / auth (OneLync's `auth.py` pattern is a reasonable template
  to copy over when needed -- not risky, skipped for now to focus on the
  calculation engine first)
- Antardasha (dasha sub-periods) -- straightforward extension of `dasha.py`
  once mahadasha output is verified
- More vargas (D2, D3, D12, D60, etc.) -- same pattern as D9/D10, add as needed
- Billing

## Running locally

```
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux
cp .env.example .env
uvicorn app.main:app --reload
```

Then open http://localhost:8000/ in a browser for the form + chart UI, or
call the API directly:

```
curl -X POST http://localhost:8000/charts/compute \
  -H "Content-Type: application/json" \
  -d '{"birth_datetime":"1990-05-14T08:30:00+05:30","latitude":28.6139,"longitude":77.2090}'
```

## Next step -- before anything else

Get 15-20 charts from your pundit (birth details + the sign/nakshatra/dasha
they'd expect), drop them into `backend/tests/fixtures/` following the
template there, and run `pytest`. This is the single highest-value thing
to do next: it tells you whether the calculation engine is trustworthy
before any UI or user gets built on top of it.
