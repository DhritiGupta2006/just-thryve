"""
DynamicRateService — computes a personalised interest rate for a loan based on
the borrower's ML risk score, ESG profile, and a configurable base rate.
"""
from decimal import Decimal


class DynamicRateService:
    # Configurable base rate (% p.a.)
    BASE_RATE: float = 12.0
    # Maximum spread above/below the base rate
    MAX_SPREAD: float = 6.0

    # ESG bonus caps
    MAX_ESG_DISCOUNT: float = 2.0

    @classmethod
    def compute_rate(
        cls,
        risk_score: int,
        renewable_mix_percent: float = 0.0,
        compliance_status: str = "pending",
        waste_recycled_percent: float = 0.0,
        social_impact_score: float = 0.0,
    ) -> float:
        """
        Return the recommended annual interest rate (%) for a borrower.

        Higher risk_score (0-1000) → lower rate.
        Better ESG metrics → additional discount on top.
        """
        # Normalise risk_score to [0, 1]
        risk_norm = max(0.0, min(1.0, risk_score / 1000.0))

        # Spread: high-risk borrowers pay MAX_SPREAD above base, low-risk get a discount
        # risk_norm=1 → -MAX_SPREAD/2  (best), risk_norm=0 → +MAX_SPREAD (worst)
        spread = cls.MAX_SPREAD * (1.0 - risk_norm) - cls.MAX_SPREAD / 2 * risk_norm
        spread = max(-cls.MAX_SPREAD / 2, min(cls.MAX_SPREAD, spread))

        # ESG discount
        esg_discount = cls._esg_discount(
            renewable_mix_percent=renewable_mix_percent,
            compliance_status=compliance_status,
            waste_recycled_percent=waste_recycled_percent,
            social_impact_score=social_impact_score,
        )

        rate = cls.BASE_RATE + spread - esg_discount
        # Clamp to a sensible lending range
        rate = max(6.0, min(24.0, rate))
        return round(rate, 4)

    @classmethod
    def _esg_discount(
        cls,
        renewable_mix_percent: float,
        compliance_status: str,
        waste_recycled_percent: float,
        social_impact_score: float,
    ) -> float:
        """Calculate ESG-based interest rate discount (%)."""
        discount = 0.0

        # Renewable energy contribution
        discount += (renewable_mix_percent / 100.0) * 0.75

        # Compliance status
        if compliance_status == "compliant":
            discount += 0.75
        elif compliance_status == "non_compliant":
            discount -= 0.5

        # Waste recycling
        discount += (waste_recycled_percent / 100.0) * 0.25

        # Social impact
        discount += (social_impact_score / 100.0) * 0.25

        return max(0.0, min(cls.MAX_ESG_DISCOUNT, discount))

    @classmethod
    def rate_breakdown(
        cls,
        risk_score: int,
        renewable_mix_percent: float = 0.0,
        compliance_status: str = "pending",
        waste_recycled_percent: float = 0.0,
        social_impact_score: float = 0.0,
    ) -> dict:
        """Return a detailed breakdown of how the rate was computed."""
        risk_norm = max(0.0, min(1.0, risk_score / 1000.0))
        spread = cls.MAX_SPREAD * (1.0 - risk_norm) - cls.MAX_SPREAD / 2 * risk_norm
        spread = max(-cls.MAX_SPREAD / 2, min(cls.MAX_SPREAD, spread))

        esg_discount = cls._esg_discount(
            renewable_mix_percent=renewable_mix_percent,
            compliance_status=compliance_status,
            waste_recycled_percent=waste_recycled_percent,
            social_impact_score=social_impact_score,
        )
        final_rate = max(6.0, min(24.0, cls.BASE_RATE + spread - esg_discount))

        return {
            "base_rate": cls.BASE_RATE,
            "risk_spread": round(spread, 4),
            "esg_discount": round(esg_discount, 4),
            "final_rate": round(final_rate, 4),
        }
