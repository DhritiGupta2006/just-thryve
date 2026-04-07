"""
DashboardService — encapsulates business logic for borrower and lender dashboard
aggregations, extracted from the dashboard router.
"""
from datetime import date
from typing import Any, Dict, List, Optional


class DashboardService:
    _ACTIVE_STATUSES = {"disbursed", "active", "submitted", "offers_received", "accepted"}

    @staticmethod
    def borrower_summary(loans: List[Any], paid_schedules: List[Any], next_emi: Optional[Any]) -> Dict:
        """
        Compute aggregated borrower dashboard data from ORM objects.

        Args:
            loans: list of Loan ORM objects (already filtered to borrower)
            paid_schedules: list of paid RepaymentSchedule ORM objects
            next_emi: earliest pending RepaymentSchedule, or None
        """
        active_statuses = DashboardService._ACTIVE_STATUSES
        active_loan_count = sum(1 for l in loans if l.status in active_statuses)
        total_requested = float(sum(l.amount_requested or 0 for l in loans))
        total_approved = float(sum(l.approved_amount or 0 for l in loans))
        total_repaid = float(sum(s.emi_amount or 0 for s in paid_schedules))

        loan_summaries = [
            {
                "loan_id": str(l.id),
                "status": l.status,
                "amount_requested": float(l.amount_requested or 0),
                "approved_amount": float(l.approved_amount) if l.approved_amount is not None else None,
                "emi_amount": float(l.emi_amount) if l.emi_amount is not None else None,
                "risk_score": l.risk_score,
                "ml_decision": l.ml_decision,
                "created_at": l.created_at.isoformat() if l.created_at else "",
            }
            for l in loans
        ]

        return {
            "loan_count": len(loans),
            "active_loan_count": active_loan_count,
            "total_requested": total_requested,
            "total_approved": total_approved,
            "total_repaid": total_repaid,
            "next_emi_date": next_emi.due_date.isoformat() if next_emi else None,
            "next_emi_amount": float(next_emi.emi_amount) if next_emi else None,
            "loans": loan_summaries,
        }

    @staticmethod
    def lender_summary(offers: List[Any]) -> Dict:
        """
        Compute aggregated lender dashboard data from ORM objects.

        Args:
            offers: list of Offer ORM objects (already filtered to lender)
        """
        accepted = [o for o in offers if o.status == "accepted"]
        portfolio_value = float(sum(o.offered_amount or 0 for o in accepted))

        rates = [float(o.interest_rate) for o in offers if o.interest_rate is not None]
        avg_rate = round(sum(rates) / len(rates), 4) if rates else None

        offer_summaries = [
            {
                "offer_id": str(o.id),
                "loan_id": str(o.loan_id),
                "status": o.status,
                "offered_amount": float(o.offered_amount or 0),
                "interest_rate": float(o.interest_rate or 0),
                "tenure_months": o.tenure_months,
                "emi_amount": float(o.emi_amount or 0),
                "created_at": o.created_at.isoformat() if o.created_at else "",
            }
            for o in offers
        ]

        return {
            "offer_count": len(offers),
            "accepted_offer_count": len(accepted),
            "portfolio_value": portfolio_value,
            "average_interest_rate": avg_rate,
            "offers": offer_summaries,
        }
