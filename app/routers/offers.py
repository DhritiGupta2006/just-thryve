from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCreateRequest, OfferResponse
from app.services.auth_service import get_current_user, require_role
from app.services.emi_service import EMIService

router = APIRouter(prefix="/offers", tags=["offers"])


def _offer_to_response(offer: Offer) -> OfferResponse:
    return OfferResponse(
        id=str(offer.id),
        loan_id=str(offer.loan_id),
        lender_id=str(offer.lender_id),
        interest_rate=offer.interest_rate,
        offered_amount=offer.offered_amount,
        tenure_months=offer.tenure_months,
        emi_amount=offer.emi_amount,
        status=offer.status,
        accepted_at=offer.accepted_at,
        expires_at=offer.expires_at,
        created_at=offer.created_at,
    )


@router.patch("/{offer_id}/accept", response_model=dict)
def accept_offer(
    offer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    """Accept a specific offer directly by offer ID (borrower only)."""
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "pending").first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or already processed")

    loan = db.query(Loan).filter(Loan.id == offer.loan_id, Loan.borrower_id == current_user.id).first()
    if not loan:
        raise HTTPException(status_code=403, detail="Access denied")
    if loan.status != "offers_received":
        raise HTTPException(status_code=400, detail="No offers available to accept")

    # Reject all other pending offers for this loan
    db.query(Offer).filter(Offer.loan_id == offer.loan_id, Offer.id != offer_id).update({"status": "rejected"})

    offer.status = "accepted"
    offer.accepted_at = datetime.utcnow()
    loan.status = "accepted"
    loan.approved_amount = offer.offered_amount
    loan.approved_rate = offer.interest_rate
    loan.emi_amount = offer.emi_amount

    db.commit()
    return {
        "offer_id": str(offer.id),
        "status": "accepted",
        "message": "Offer accepted successfully",
    }


@router.get("", response_model=List[OfferResponse])
def list_offers(
    loan_id: str = Query(..., description="UUID of the loan"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    # Borrowers can only see offers for their own loans
    if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    offers = db.query(Offer).filter(Offer.loan_id == loan_id).all()
    return [_offer_to_response(o) for o in offers]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_offer(
    payload: OfferCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("lender")),
):
    loan = db.query(Loan).filter(Loan.id == payload.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status not in ("submitted", "offers_received"):
        raise HTTPException(status_code=400, detail=f"Loan is not accepting offers (status: {loan.status})")

    emi = EMIService.calculate_emi(
        float(payload.offered_amount),
        float(payload.interest_rate),
        payload.tenure_months,
    )

    offer = Offer(
        loan_id=loan.id,
        lender_id=current_user.id,
        interest_rate=payload.interest_rate,
        offered_amount=payload.offered_amount,
        tenure_months=payload.tenure_months,
        emi_amount=emi,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(offer)

    # Transition loan to offers_received if not already
    if loan.status == "submitted":
        loan.status = "offers_received"

    db.commit()
    db.refresh(offer)
    return {"offer_id": str(offer.id)}
