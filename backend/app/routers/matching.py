from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import ephemeris, matching
from app.schemas import MatchRequest, MatchResponse, PersonBirth

router = APIRouter(prefix="/matching", tags=["matching"])


def _bodies_for(person: PersonBirth, ayanamsa: str, node_type: str) -> dict:
    try:
        birth_dt = geocode.ensure_aware(person.birth_datetime, person.latitude, person.longitude)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    positions = ephemeris.compute_positions(
        dt_utc=birth_dt,
        lat=person.latitude,
        lon=person.longitude,
        ayanamsa=ayanamsa,
        node_type=node_type,
    )
    return positions["bodies"]


@router.post("/compute", response_model=MatchResponse)
def compute_match(request: MatchRequest):
    bride_bodies = _bodies_for(request.bride, request.ayanamsa, request.node_type)
    groom_bodies = _bodies_for(request.groom, request.ayanamsa, request.node_type)

    result = matching.ashtakoot(bride_bodies, groom_bodies)

    return MatchResponse(
        **result,
        bride_moon={
            "sign": bride_bodies["Moon"]["sign"],
            "nakshatra": bride_bodies["Moon"]["nakshatra"],
        },
        groom_moon={
            "sign": groom_bodies["Moon"]["sign"],
            "nakshatra": groom_bodies["Moon"]["nakshatra"],
        },
    )
