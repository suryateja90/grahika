from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import dasha, ephemeris, vargas
from app.schemas import ChartRequest, ChartResponse

router = APIRouter(prefix="/charts", tags=["charts"])


@router.post("/compute", response_model=ChartResponse)
def compute_chart(request: ChartRequest):
    birth_dt = request.birth_datetime
    if birth_dt.tzinfo is None:
        # No explicit UTC offset given -- resolve the historical local
        # timezone for this place/date instead of guessing. This is what
        # makes place-name-only input (no lat/lon or offset known by the
        # user) safe to use.
        try:
            birth_dt = geocode.localize(birth_dt, request.latitude, request.longitude)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    positions = ephemeris.compute_positions(
        dt_utc=birth_dt,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )

    varga_charts = vargas.compute_vargas(positions["bodies"])

    moon_longitude = positions["bodies"]["Moon"]["longitude"]
    dasha_timeline = dasha.vimshottari_timeline(
        moon_longitude, birth_dt, cycles=request.dasha_cycles
    )

    return ChartResponse(
        julian_day=positions["julian_day"],
        ayanamsa=positions["ayanamsa"],
        ayanamsa_value=positions["ayanamsa_value"],
        positions=positions["bodies"],
        vargas=varga_charts,
        vimshottari_dasha=dasha_timeline,
    )
