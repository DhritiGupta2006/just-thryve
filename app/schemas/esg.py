from typing import Optional

from pydantic import BaseModel, Field


class ESGMetricsResponse(BaseModel):
    renewable_energy_percent: float
    carbon_intensity: float
    compliance_score: int
    waste_recycled_percent: float
    social_impact_score: float

    class Config:
        from_attributes = True


class ESGMetricsUpdate(BaseModel):
    renewable_energy_percent: Optional[float] = Field(None, ge=0, le=100)
    carbon_intensity: Optional[float] = Field(None, ge=0)
    waste_recycled_percent: Optional[float] = Field(None, ge=0, le=100)
    social_impact_score: Optional[float] = Field(None, ge=0, le=100)
