from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business_profile import BusinessProfile
from app.models.user import User
from app.services.auth_service import require_role

router = APIRouter(prefix="/esg", tags=["esg"])

# Map compliance_status string to a numeric score
_COMPLIANCE_SCORE: dict[str, int] = {
    "compliant": 100,
    "pending": 60,
    "non_compliant": 20,
}


class ESGMetricsResponse(BaseModel):
    renewable_energy_percent: float
    carbon_intensity: float
    compliance_score: int
    waste_recycled_percent: float
    social_impact_score: float

    class Config:
        from_attributes = True


@router.get("/metrics", response_model=ESGMetricsResponse)
def get_esg_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    """Return ESG metrics for the authenticated borrower's business profile.

    Fields sourced directly from the business profile:
      * renewable_energy_percent  — renewable_mix_percent column
      * carbon_intensity          — carbon_emissions_tons column
      * compliance_score          — derived from compliance_status enum

    Fields not yet persisted in the database are returned as 0.0 so the
    frontend can display them and fill them in once data collection is added.
    """
    profile = (
        db.query(BusinessProfile)
        .filter(BusinessProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    return ESGMetricsResponse(
        renewable_energy_percent=float(profile.renewable_mix_percent or 0),
        carbon_intensity=float(profile.carbon_emissions_tons or 0),
        compliance_score=_COMPLIANCE_SCORE.get(profile.compliance_status or "pending", 60),
        waste_recycled_percent=0.0,
        social_impact_score=0.0,
    )
