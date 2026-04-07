"""
LoanComparisonService — compares multiple loan offers side-by-side and
provides a recommendation based on total cost, rate, and tenure.
"""
from decimal import Decimal
from typing import Any, Dict, List

from app.services.emi_service import EMIService


class LoanComparisonService:
    @staticmethod
    def compare_offers(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Accept a list of offer dicts (each with offered_amount, interest_rate,
        tenure_months, emi_amount) and return a comparison with recommendation.

        Each offer should have:
          - offer_id: str
          - lender_id: str
          - offered_amount: float
          - interest_rate: float  (annual %)
          - tenure_months: int
          - emi_amount: float
          - status: str
        """
        if not offers:
            return {"comparisons": [], "recommended_offer_id": None, "summary": "No offers available."}

        comparisons = []
        for offer in offers:
            amount = float(offer.get("offered_amount", 0))
            rate = float(offer.get("interest_rate", 0))
            tenure = int(offer.get("tenure_months", 12))
            emi = float(offer.get("emi_amount", 0))

            total_payment = round(emi * tenure, 2)
            total_interest = round(total_payment - amount, 2)
            effective_monthly_rate = round(rate / 12 / 100, 6)

            comparisons.append({
                "offer_id": str(offer.get("offer_id") or offer.get("id", "")),
                "lender_id": str(offer.get("lender_id", "")),
                "offered_amount": amount,
                "interest_rate": rate,
                "tenure_months": tenure,
                "emi_amount": emi,
                "total_payment": total_payment,
                "total_interest_paid": total_interest,
                "effective_monthly_rate": effective_monthly_rate,
                "status": offer.get("status", ""),
            })

        # Recommend the offer with lowest total cost among pending offers
        pending = [c for c in comparisons if c["status"] == "pending"]
        if not pending:
            pending = comparisons  # fallback: consider all

        recommended = min(pending, key=lambda c: c["total_payment"])
        recommended_id = recommended["offer_id"]

        # Build summary
        best_rate = min(c["interest_rate"] for c in comparisons)
        worst_rate = max(c["interest_rate"] for c in comparisons)
        savings = round(
            max(c["total_payment"] for c in comparisons if c["status"] in ("pending", ""))
            - recommended["total_payment"],
            2,
        ) if len(pending) > 1 else 0.0

        summary = (
            f"{len(comparisons)} offer(s) available. "
            f"Rates range from {best_rate}% to {worst_rate}% p.a. "
        )
        if savings > 0:
            summary += f"The recommended offer saves ₹{savings:,.2f} in total interest."

        return {
            "comparisons": comparisons,
            "recommended_offer_id": recommended_id,
            "summary": summary,
        }

    @staticmethod
    def early_repayment_summary(
        outstanding_principal: float,
        annual_rate_percent: float,
        remaining_months: int,
        prepayment_amount: float,
        prepayment_penalty_percent: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Compute the impact of an early/partial prepayment.

        Returns savings vs. continuing the original schedule.
        """
        # Original schedule: total remaining payments
        original_emi = EMIService.calculate_emi(
            outstanding_principal, annual_rate_percent, remaining_months
        )
        original_total = round(original_emi * remaining_months, 2)

        # After prepayment
        penalty = round(prepayment_amount * prepayment_penalty_percent / 100, 2)
        new_principal = max(0.0, outstanding_principal - prepayment_amount)

        if new_principal <= 0:
            new_total = prepayment_amount + penalty
            new_emi = 0.0
            new_months = 0
        else:
            new_emi = EMIService.calculate_emi(
                new_principal, annual_rate_percent, remaining_months
            )
            new_total = round(prepayment_amount + penalty + new_emi * remaining_months, 2)
            new_months = remaining_months

        savings = round(original_total - new_total, 2)

        return {
            "outstanding_principal": outstanding_principal,
            "prepayment_amount": prepayment_amount,
            "prepayment_penalty": penalty,
            "original_total_remaining": original_total,
            "new_total_remaining": new_total,
            "estimated_savings": max(0.0, savings),
            "new_emi": new_emi,
            "remaining_months_after_prepayment": new_months,
            "fully_repaid": new_principal <= 0,
        }
