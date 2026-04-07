"""
Notifications endpoint.

Generates real-time notifications derived from the authenticated user's
loan lifecycle and repayment schedule, rather than storing a separate
notifications table. This keeps the backend in sync with actual data.
"""
from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.offer import Offer
from app.models.repayment_schedule import RepaymentSchedule
from app.models.user import User
from app.schemas.notifications import NotificationResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _iso(dt) -> str:
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, date):
        return datetime(dt.year, dt.month, dt.day).isoformat()
    return ""


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return notifications derived from the user's recent loan and repayment activity."""
    notes: List[NotificationResponse] = []
    today = date.today()

    if current_user.role == "borrower":
        loans: List[Loan] = (
            db.query(Loan)
            .filter(Loan.borrower_id == current_user.id)
            .order_by(Loan.created_at.desc())
            .limit(20)
            .all()
        )
        loan_ids = [l.id for l in loans]

        # Notify about each loan status milestone
        for loan in loans:
            if loan.status == "submitted" and loan.submitted_at:
                notes.append(NotificationResponse(
                    id=f"loan-submitted-{loan.id}",
                    title="Loan Application Submitted",
                    description=(
                        f"Your loan application for ₹{float(loan.amount_requested):,.0f} "
                        "is under review by our AI underwriting engine."
                    ),
                    category="Loan",
                    created_at=_iso(loan.submitted_at),
                ))
            if loan.status in ("offers_received", "accepted", "disbursed", "active", "closed"):
                notes.append(NotificationResponse(
                    id=f"loan-status-{loan.id}-{loan.status}",
                    title=f"Loan Status: {loan.status.replace('_', ' ').title()}",
                    description=(
                        f"Your loan application for ₹{float(loan.amount_requested):,.0f} "
                        f"has moved to status '{loan.status}'."
                    ),
                    category="Loan",
                    created_at=_iso(loan.disbursed_at or loan.submitted_at or loan.created_at),
                ))

        # Upcoming EMI reminders (due within next 7 days)
        if loan_ids:
            upcoming: List[RepaymentSchedule] = (
                db.query(RepaymentSchedule)
                .filter(
                    RepaymentSchedule.loan_id.in_(loan_ids),
                    RepaymentSchedule.status == "pending",
                    RepaymentSchedule.due_date >= today,
                    RepaymentSchedule.due_date <= today + timedelta(days=7),
                )
                .order_by(RepaymentSchedule.due_date)
                .all()
            )
            for s in upcoming:
                notes.append(NotificationResponse(
                    id=f"emi-due-{s.id}",
                    title="Upcoming EMI Payment",
                    description=(
                        f"EMI of ₹{float(s.emi_amount):,.0f} is due on {s.due_date}. "
                        "Please ensure sufficient balance."
                    ),
                    category="Financial",
                    created_at=_iso(s.due_date),
                ))

            # Overdue installments
            overdue: List[RepaymentSchedule] = (
                db.query(RepaymentSchedule)
                .filter(
                    RepaymentSchedule.loan_id.in_(loan_ids),
                    RepaymentSchedule.status == "pending",
                    RepaymentSchedule.due_date < today,
                )
                .order_by(RepaymentSchedule.due_date)
                .all()
            )
            for s in overdue:
                notes.append(NotificationResponse(
                    id=f"emi-overdue-{s.id}",
                    title="Overdue EMI",
                    description=(
                        f"EMI of ₹{float(s.emi_amount):,.0f} was due on {s.due_date} "
                        "and has not been paid."
                    ),
                    category="Financial",
                    created_at=_iso(s.due_date),
                ))

    else:  # lender
        offers: List[Offer] = (
            db.query(Offer)
            .filter(Offer.lender_id == current_user.id)
            .order_by(Offer.created_at.desc())
            .limit(20)
            .all()
        )
        for offer in offers:
            if offer.status == "accepted":
                notes.append(NotificationResponse(
                    id=f"offer-accepted-{offer.id}",
                    title="Offer Accepted",
                    description=(
                        f"Your offer of ₹{float(offer.offered_amount):,.0f} "
                        f"at {float(offer.interest_rate):.2f}% p.a. has been accepted by the borrower."
                    ),
                    category="Offers",
                    created_at=_iso(offer.accepted_at or offer.created_at),
                ))
            elif offer.status == "rejected":
                notes.append(NotificationResponse(
                    id=f"offer-rejected-{offer.id}",
                    title="Offer Not Selected",
                    description=(
                        f"Your offer of ₹{float(offer.offered_amount):,.0f} "
                        "was not selected by the borrower."
                    ),
                    category="Offers",
                    created_at=_iso(offer.created_at),
                ))

    # Sort by created_at descending
    notes.sort(key=lambda n: n.created_at, reverse=True)
    return notes
