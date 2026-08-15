from datetime import datetime

import pytz
from fastapi import APIRouter, HTTPException

from app import geocode
from app.astro import ephemeris, transits
from app.schemas import TransitRequest, TransitResponse

router = APIRouter(prefix="/transits", tags=["transits"])

# The Moon moves ~13 degrees/day and can change sign mid-day, so the time
# a daily report is cast for genuinely matters. Noon local is the
# conventional choice: it is stable, reproducible, and sits in the middle
# of the waking day rather than favouring either end of it.
REPORT_HOUR = 12


@router.post("/daily", response_model=TransitResponse)
def daily_transit(request: TransitRequest):
    try:
        birth_dt = geocode.ensure_aware(request.birth_datetime, request.latitude, request.longitude)
        tz = pytz.timezone(geocode.timezone_name_for(request.latitude, request.longitude))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    report_date = request.transit_date or datetime.now(tz).date()

    if request.transit_time:
        parts = [int(p) for p in request.transit_time.split(":")]
        hour, minute = parts[0], parts[1]
        second = parts[2] if len(parts) > 2 else 0
    else:
        hour, minute, second = REPORT_HOUR, 0, 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise HTTPException(status_code=422, detail="transit_time must be a valid 24-hour clock time")

    transit_dt = tz.localize(
        datetime(report_date.year, report_date.month, report_date.day, hour, minute, second)
    )

    natal = ephemeris.compute_positions(
        dt_utc=birth_dt,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )["bodies"]

    # Transit positions are location-independent for the grahas; the natal
    # coordinates are passed only because the Ascendant calculation needs
    # them, and the transit Ascendant is not used in this report.
    transit = ephemeris.compute_positions(
        dt_utc=transit_dt,
        lat=request.latitude,
        lon=request.longitude,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )["bodies"]

    report = transits.daily_report(natal, transit)
    return TransitResponse(
        transit_date=report_date.isoformat(),
        transit_time=transit_dt.strftime("%H:%M"),
        **report,
    )
