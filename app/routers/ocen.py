"""
OCEN (Open Credit Enablement Network) simulation endpoints.

In production these would integrate with a real OCEN gateway.
Here they provide mock network interactions for development and testing.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.models.business_profile import BusinessProfile
from app.services.auth_service import get_current_user
from app.services.ocen_simulation_service import OCENSimulationService

router = APIRouter(prefix="/ocen", tags=["ocen"])


# ---------------------------------------------------------------------------
# Response schemas (OCEN-specific, small, kept inline)
# ---------------------------------------------------------------------------

class NetworkStatusResponse(BaseModel):
    network_id: str
    status: str
    protocol_version: str
    registered_lenders: int
    active_lenders: int
    timestamp: str
    features: List[str]


class LenderDiscoveryItem(BaseModel):
    lender_id: str
    name: str
    type: str
    specialisation: List[str]
    min_loan: float
    max_loan: float
    base_rate_pct: float
    active: bool
    sector_match: bool
    indicative_rate_pct: float
    estimated_emi: float


class BroadcastResponse(BaseModel):
    broadcast_id: str
    loan_id: str
    notified_lender_count: int
    notified_lenders: List[str]
    broadcast_at: str
    response_deadline: str
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/network-status", response_model=NetworkStatusResponse)
def get_network_status(
    current_user: User = Depends(get_current_user),
):
    """Return the current status of the OCEN network."""
    return OCENSimulationService.network_status()


@router.get("/discover-lenders", response_model=List[LenderDiscoveryItem])
def discover_lenders(
    loan_amount: float = Query(..., gt=0, description="Requested loan amount in INR"),
    sector: str = Query("commerce", description="Business sector: renewable_energy, agriculture, commerce"),
    tenure_months: int = Query(12, ge=1, le=360, description="Desired loan tenure in months"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Discover eligible lenders on the OCEN network for a given loan request.

    Any authenticated user can call this endpoint to explore available lenders.
    """
    valid_sectors = {"renewable_energy", "agriculture", "commerce"}
    if sector not in valid_sectors:
        raise HTTPException(
            status_code=400,
            detail=f"sector must be one of {valid_sectors}",
        )
    lenders = OCENSimulationService.discover_lenders(
        loan_amount=loan_amount,
        sector=sector,
        tenure_months=tenure_months,
    )
    return lenders


@router.post("/broadcast/{loan_id}", response_model=BroadcastResponse)
def broadcast_loan_request(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Broadcast a submitted loan request to all eligible lenders on the OCEN network.

    Only the borrower who owns the loan may trigger a broadcast.
    The loan must be in 'submitted' or 'offers_received' status.
    """
    loan: Optional[Loan] = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    if loan.status not in ("submitted", "offers_received"):
        raise HTTPException(
            status_code=400,
            detail=f"Loan must be in 'submitted' or 'offers_received' status to broadcast (current: {loan.status})",
        )

    # Determine sector from borrower's business profile
    profile: Optional[BusinessProfile] = (
        db.query(BusinessProfile)
        .filter(BusinessProfile.user_id == loan.borrower_id)
        .first()
    )
    sector = profile.sector if profile else "commerce"

    result = OCENSimulationService.broadcast_loan_request(
        loan_id=str(loan.id),
        loan_amount=float(loan.amount_requested),
        sector=sector,
    )
    return result
