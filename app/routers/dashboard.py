from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.offer import Offer
from app.models.repayment_schedule import RepaymentSchedule
from app.models.user import User
from app.schemas.dashboard import (
    BorrowerDashboardResponse,
    LenderDashboardResponse,
    LoanSummary,
    OfferSummary,
)
from app.services.auth_service import require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Borrower dashboard
# ---------------------------------------------------------------------------


@router.get("/borrower", response_model=BorrowerDashboardResponse)
def borrower_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    """Aggregated dashboard data for a borrower."""
    loans: List[Loan] = (
        db.query(Loan)
        .filter(Loan.borrower_id == current_user.id)
        .order_by(Loan.created_at.desc())
        .all()
    )

    active_statuses = {"disbursed", "active", "submitted", "offers_received", "accepted"}
    active_loan_count = sum(1 for l in loans if l.status in active_statuses)
    total_requested = float(sum(l.amount_requested or 0 for l in loans))
    total_approved = float(sum(l.approved_amount or 0 for l in loans))

    # Sum all paid repayment installments across all borrower loans
    loan_ids = [l.id for l in loans]
    paid_schedules: List[RepaymentSchedule] = []
    if loan_ids:
        paid_schedules = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.loan_id.in_(loan_ids),
                RepaymentSchedule.status == "paid",
            )
            .all()
        )
    total_repaid = float(sum(s.emi_amount or 0 for s in paid_schedules))

    # Find the earliest upcoming EMI
    next_emi: Optional[RepaymentSchedule] = None
    if loan_ids:
        next_emi = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.loan_id.in_(loan_ids),
                RepaymentSchedule.status == "pending",
            )
            .order_by(RepaymentSchedule.due_date)
            .first()
        )

    loan_summaries = [
        LoanSummary(
            loan_id=str(l.id),
            status=l.status,
            amount_requested=float(l.amount_requested or 0),
            approved_amount=float(l.approved_amount) if l.approved_amount is not None else None,
            emi_amount=float(l.emi_amount) if l.emi_amount is not None else None,
            risk_score=l.risk_score,
            ml_decision=l.ml_decision,
            created_at=l.created_at.isoformat() if l.created_at else "",
        )
        for l in loans
    ]

    return BorrowerDashboardResponse(
        loan_count=len(loans),
        active_loan_count=active_loan_count,
        total_requested=total_requested,
        total_approved=total_approved,
        total_repaid=total_repaid,
        next_emi_date=next_emi.due_date.isoformat() if next_emi else None,
        next_emi_amount=float(next_emi.emi_amount) if next_emi else None,
        loans=loan_summaries,
    )


# ---------------------------------------------------------------------------
# Lender dashboard
# ---------------------------------------------------------------------------


@router.get("/lender", response_model=LenderDashboardResponse)
def lender_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("lender")),
):
    """Aggregated dashboard data for a lender."""
    offers: List[Offer] = (
        db.query(Offer)
        .filter(Offer.lender_id == current_user.id)
        .order_by(Offer.created_at.desc())
        .all()
    )

    accepted = [o for o in offers if o.status == "accepted"]
    portfolio_value = float(sum(o.offered_amount or 0 for o in accepted))

    rates = [float(o.interest_rate) for o in offers if o.interest_rate is not None]
    avg_rate = round(sum(rates) / len(rates), 4) if rates else None

    offer_summaries = [
        OfferSummary(
            offer_id=str(o.id),
            loan_id=str(o.loan_id),
            status=o.status,
            offered_amount=float(o.offered_amount or 0),
            interest_rate=float(o.interest_rate or 0),
            tenure_months=o.tenure_months,
            emi_amount=float(o.emi_amount or 0),
            created_at=o.created_at.isoformat() if o.created_at else "",
        )
        for o in offers
    ]

    return LenderDashboardResponse(
        offer_count=len(offers),
        accepted_offer_count=len(accepted),
        portfolio_value=portfolio_value,
        average_interest_rate=avg_rate,
        offers=offer_summaries,
    )
