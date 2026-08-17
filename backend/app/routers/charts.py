from datetime import datetime

from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import avakhada, dasha, doshas, ephemeris, vargas
from app.schemas import ChartRequest, ChartResponse, DoshaResponse

router = APIRouter(prefix="/charts", tags=["charts"])


def _resolve_birth_datetime(request: ChartRequest):
    # A naive datetime means no UTC offset was supplied -- resolve the
    # historical local timezone for this place/date rather than guessing.
    # This is what makes place-name-only input safe to use.
    try:
        return geocode.ensure_aware(request.birth_datetime, request.latitude, request.longitude)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/compute", response_model=ChartResponse)
def compute_chart(request: ChartRequest):
    birth_dt = _resolve_birth_datetime(request)

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

    # "Now" for the running period is the user's clock, not the server's.
    now = datetime.now(birth_dt.tzinfo)

    return ChartResponse(
        julian_day=positions["julian_day"],
        ayanamsa=positions["ayanamsa"],
        ayanamsa_value=positions["ayanamsa_value"],
        positions=positions["bodies"],
        vargas=varga_charts,
        vimshottari_dasha=dasha_timeline,
        avakhada=avakhada.avakhada_chakra(positions["bodies"]),
        natal_aspects=avakhada.natal_aspects(positions["bodies"]),
        current_periods=dasha.current_periods(dasha_timeline, now),
    )


@router.post("/doshas", response_model=DoshaResponse)
def compute_doshas(request: ChartRequest):
    birth_dt = _resolve_birth_datetime(request)

    positions = ephemeris.compute_positions(
        dt_utc=birth_dt,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )

    kaal_sarp = doshas.kaal_sarp_yoga(positions["bodies"])
    moon_sign_index = positions["bodies"]["Moon"]["sign_index"]
    sade_sati = doshas.sade_sati_status(moon_sign_index, ayanamsa=request.ayanamsa)

    return DoshaResponse(kaal_sarp_yoga=kaal_sarp, sade_sati=sade_sati)
