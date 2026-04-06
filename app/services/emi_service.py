"""
Dynamic EMI calculation engine using the standard reducing-balance formula.
"""
from decimal import Decimal, ROUND_HALF_UP
import math


class EMIService:
    @staticmethod
    def calculate_emi(principal: float, annual_rate_percent: float, tenure_months: int) -> float:
        """
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        where r = monthly interest rate, n = tenure in months
        """
        if tenure_months <= 0:
            raise ValueError("Tenure must be positive")
        if annual_rate_percent <= 0:
            # Interest-free loan
            return round(principal / tenure_months, 2)

        monthly_rate = annual_rate_percent / 12 / 100
        factor = (1 + monthly_rate) ** tenure_months
        emi = principal * monthly_rate * factor / (factor - 1)
        return round(emi, 2)

    @staticmethod
    def generate_amortization_schedule(
        principal: float,
        annual_rate_percent: float,
        tenure_months: int,
    ) -> list[dict]:
        """
        Returns a list of installment dicts with principal, interest, and emi breakdown.
        """
        emi = EMIService.calculate_emi(principal, annual_rate_percent, tenure_months)
        monthly_rate = annual_rate_percent / 12 / 100
        balance = principal
        schedule = []

        for i in range(1, tenure_months + 1):
            interest_component = round(balance * monthly_rate, 2)
            principal_component = round(emi - interest_component, 2)
            # Adjust last installment for rounding drift
            if i == tenure_months:
                principal_component = round(balance, 2)
                emi_adjusted = round(principal_component + interest_component, 2)
            else:
                emi_adjusted = emi
            balance = round(balance - principal_component, 2)
            schedule.append(
                {
                    "installment_number": i,
                    "principal_amount": principal_component,
                    "interest_amount": interest_component,
                    "emi_amount": emi_adjusted,
                }
            )

        return schedule
