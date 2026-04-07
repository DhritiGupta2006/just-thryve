from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class BusinessProfileCreate(BaseModel):
    business_name: str
    sector: str  # renewable_energy, agriculture, commerce
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    avg_gst_revenue_3m: Optional[Decimal] = None
    renewable_mix_percent: Optional[int] = 0
    carbon_emissions_tons: Optional[Decimal] = None
    compliance_status: Optional[str] = "pending"
    waste_recycled_percent: Optional[Decimal] = None
    social_impact_score: Optional[Decimal] = None


class BusinessProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    sector: Optional[str] = None
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    avg_gst_revenue_3m: Optional[Decimal] = None
    renewable_mix_percent: Optional[int] = None
    carbon_emissions_tons: Optional[Decimal] = None
    compliance_status: Optional[str] = None
    waste_recycled_percent: Optional[Decimal] = None
    social_impact_score: Optional[Decimal] = None


class BusinessProfileResponse(BaseModel):
    id: str
    user_id: str
    business_name: str
    sector: str
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    avg_gst_revenue_3m: Optional[Decimal] = None
    renewable_mix_percent: int
    carbon_emissions_tons: Optional[Decimal] = None
    compliance_status: str
    waste_recycled_percent: Decimal
    social_impact_score: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
