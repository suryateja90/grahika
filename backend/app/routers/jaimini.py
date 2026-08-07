from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import ephemeris, jaimini, vargas
from app.schemas import ChartRequest, IshtaDevataResponse

router = APIRouter(prefix="/jaimini", tags=["jaimini"])


@router.post("/ishta-devata", response_model=IshtaDevataResponse)
def compute_ishta_devata(request: ChartRequest):
    try:
        birth_dt = geocode.ensure_aware(request.birth_datetime, request.latitude, request.longitude)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    bodies = ephemeris.compute_positions(
        dt_utc=birth_dt,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )["bodies"]

    return IshtaDevataResponse(**jaimini.ishta_devata(bodies, vargas.compute_vargas(bodies)))
