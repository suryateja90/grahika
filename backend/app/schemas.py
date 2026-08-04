from datetime import datetime
from typing import Literal

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
    vimshottari_dasha: list


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


class MatchResponse(BaseModel):
    kootas: list
    total: float
    max_total: int
    interpretation: str
    bride_mangal: dict
    groom_mangal: dict
    bride_moon: dict
    groom_moon: dict
