from fastapi import APIRouter, HTTPException, Query

from app import geocode

router = APIRouter(prefix="/geocode", tags=["geocode"])


@router.get("/search")
def search(q: str = Query(..., min_length=2)):
    try:
        return geocode.search_places(q)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Place lookup failed: {e}")


@router.get("/reverse")
def reverse(lat: float, lon: float):
    try:
        return geocode.reverse_geocode(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reverse lookup failed: {e}")
