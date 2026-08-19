from datetime import date, datetime
from datetime import date as date_type  # see PanchangaRequest.date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChartRequest(BaseModel):
    birth_datetime: datetime = Field(..., description="Local birth date/time, timezone-aware ISO 8601")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    ayanamsa: Literal["lahiri", "raman", "kp", "true_chitra"] = "lahiri"
    node_type: Literal["mean", "true"] = "mean"
    dasha_cycles: int = Field(1, ge=1, le=2, description="Number of 120-year Vimshottari cycles to return")


class ChartResponse(BaseModel):
    julian_day: float
    ayanamsa: str
    ayanamsa_value: float
    positions: dict
    vargas: dict
    varga_houses: dict
    vimshottari_dasha: list
    avakhada: dict
    natal_aspects: dict
    current_periods: dict


class DoshaResponse(BaseModel):
    kaal_sarp_yoga: dict
    sade_sati: dict


class PersonBirth(BaseModel):
    name: str = ""
    birth_datetime: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class MatchRequest(BaseModel):
    bride: PersonBirth
    groom: PersonBirth
    ayanamsa: Literal["lahiri", "raman", "kp", "true_chitra"] = "lahiri"
    node_type: Literal["mean", "true"] = "mean"


class TransitRequest(BaseModel):
    birth_datetime: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    ayanamsa: Literal["lahiri", "raman", "kp", "true_chitra"] = "lahiri"
    node_type: Literal["mean", "true"] = "mean"
    transit_date: Optional[date] = Field(
        None, description="Date to report on; defaults to today in the birth place's timezone"
    )
    transit_time: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Local clock time to cast for, HH:MM. Defaults to 12:00 noon.",
    )


class TransitResponse(BaseModel):
    transit_date: str
    transit_time: str
    natal_moon: dict
    transit_moon: dict
    summary: dict
    tara_bala: dict
    chandra_bala: dict
    planet_transits: list
    aspects: list
    natal_chart: dict
    transit_chart: dict


class IshtaDevataResponse(BaseModel):
    atmakaraka: str
    atmakaraka_degree: float
    karakamsha_sign_index: int
    twelfth_sign_index: int
    occupants: list
    indicator_planet: str
    basis: str
    deity: dict
    karakas: list
    scheme: str


class PanchangaRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    # date_type, not date: for `x: ann = val` CPython assigns the value
    # before evaluating the annotation, so by the time Optional[...] is
    # evaluated the name `date` in this class body is already the FieldInfo.
    date: Optional[date_type] = Field(None, description="Defaults to today in the place's timezone")
    ayanamsa: Literal["lahiri", "raman", "kp", "true_chitra"] = "lahiri"


class PanchangaResponse(BaseModel):
    date: str
    vara: dict
    masa: dict
    tithi: dict
    nakshatra: dict
    yoga: dict
    karana: dict
    # The same limbs across the calendar day, so the page can show what
    # follows as well as what is in force at sunrise.
    tithis: list
    nakshatras: list
    yogas: list
    karanas: list
    sunrise: Optional[str]
    sunset: Optional[str]
    moonrise: Optional[str]
    moonset: Optional[str]
    day_length_minutes: Optional[int]
    sun_sign: dict
    moon_sign: dict
    lagna: dict
    moon_phase: dict
    dishashool: str
    festivals: list
    sankranti: Optional[dict]
    periods: dict
    varjyam_is_conventional: bool


class MatchResponse(BaseModel):
    kootas: list
    total: float
    max_total: int
    interpretation: str
    bride_mangal: dict
    groom_mangal: dict
    bride_moon: dict
    groom_moon: dict
