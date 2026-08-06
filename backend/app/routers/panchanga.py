from datetime import datetime

import pytz
from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import panchanga
from app.schemas import PanchangaRequest, PanchangaResponse

router = APIRouter(prefix="/panchanga", tags=["panchanga"])


@router.post("/daily", response_model=PanchangaResponse)
def daily_panchanga(request: PanchangaRequest):
    try:
        tz = pytz.timezone(geocode.timezone_name_for(request.latitude, request.longitude))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # "Today" means today where the user is, not UTC -- a panchangam read
    # after 18:30 IST would otherwise still show the previous day.
    report_date = request.date or datetime.now(tz).date()

    return PanchangaResponse(**panchanga.compute_panchanga(
        report_date, request.latitude, request.longitude, tz, request.ayanamsa
    ))
