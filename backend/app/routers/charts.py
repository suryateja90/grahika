from fastapi import APIRouter, HTTPException

from app.astro import dasha, ephemeris, vargas
from app.schemas import ChartRequest, ChartResponse

router = APIRouter(prefix="/charts", tags=["charts"])


@router.post("/compute", response_model=ChartResponse)
def compute_chart(request: ChartRequest):
    if request.birth_datetime.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="birth_datetime must include a UTC offset, e.g. 1990-05-14T08:30:00+05:30",
        )

    positions = ephemeris.compute_positions(
        dt_utc=request.birth_datetime,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )

    varga_charts = vargas.compute_vargas(positions["bodies"])

    moon_longitude = positions["bodies"]["Moon"]["longitude"]
    dasha_timeline = dasha.vimshottari_timeline(
        moon_longitude, request.birth_datetime, cycles=request.dasha_cycles
    )

    return ChartResponse(
        julian_day=positions["julian_day"],
        ayanamsa=positions["ayanamsa"],
        ayanamsa_value=positions["ayanamsa_value"],
        positions=positions["bodies"],
        vargas=varga_charts,
        vimshottari_dasha=dasha_timeline,
    )
