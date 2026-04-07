from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business_profile import BusinessProfile
from app.models.user import User
from app.schemas.esg import ESGMetricsResponse, ESGMetricsUpdate
from app.services.auth_service import require_role

router = APIRouter(prefix="/esg", tags=["esg"])

# Map compliance_status string to a numeric score
_COMPLIANCE_SCORE: dict[str, int] = {
    "compliant": 100,
    "pending": 60,
    "non_compliant": 20,
}


@router.get("/metrics", response_model=ESGMetricsResponse)
def get_esg_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    """Return ESG metrics for the authenticated borrower's business profile."""
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
        waste_recycled_percent=float(profile.waste_recycled_percent or 0),
        social_impact_score=float(profile.social_impact_score or 0),
    )


@router.put("/metrics", response_model=ESGMetricsResponse)
def update_esg_metrics(
    payload: ESGMetricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    """Update ESG metrics for the authenticated borrower's business profile."""
    profile = (
        db.query(BusinessProfile)
        .filter(BusinessProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    if payload.renewable_energy_percent is not None:
        profile.renewable_mix_percent = int(payload.renewable_energy_percent)
    if payload.carbon_intensity is not None:
        profile.carbon_emissions_tons = payload.carbon_intensity
    if payload.waste_recycled_percent is not None:
        profile.waste_recycled_percent = payload.waste_recycled_percent
    if payload.social_impact_score is not None:
        profile.social_impact_score = payload.social_impact_score

    db.commit()
    db.refresh(profile)

    return ESGMetricsResponse(
        renewable_energy_percent=float(profile.renewable_mix_percent or 0),
        carbon_intensity=float(profile.carbon_emissions_tons or 0),
        compliance_score=_COMPLIANCE_SCORE.get(profile.compliance_status or "pending", 60),
        waste_recycled_percent=float(profile.waste_recycled_percent or 0),
        social_impact_score=float(profile.social_impact_score or 0),
    )
