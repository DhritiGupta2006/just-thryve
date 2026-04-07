"""
RiskExplanationService — translates raw SHAP values from an ML audit log
into human-readable risk factor explanations for borrowers and lenders.
"""
from typing import Any, Dict, List, Optional


# Human-readable labels and thresholds for each feature
_FEATURE_META: Dict[str, Dict[str, Any]] = {
    "gst_revenue_3m_avg": {
        "label": "Average GST Revenue (3-month)",
        "positive_msg": "Strong average revenue supports repayment capacity.",
        "negative_msg": "Low average revenue raises concerns about repayment capacity.",
        "unit": "₹",
    },
    "gst_revenue_growth_rate": {
        "label": "Revenue Growth Rate",
        "positive_msg": "Positive revenue growth trend is a strong indicator.",
        "negative_msg": "Declining revenue is a risk factor.",
        "unit": "%",
    },
    "gst_revenue_volatility": {
        "label": "Revenue Volatility",
        "positive_msg": "Stable revenue reduces repayment risk.",
        "negative_msg": "High revenue volatility increases repayment uncertainty.",
        "unit": "₹",
    },
    "renewable_energy_mix": {
        "label": "Renewable Energy Mix",
        "positive_msg": "High renewable energy usage positively impacts ESG score.",
        "negative_msg": "Low renewable energy usage affects ESG profile.",
        "unit": "%",
    },
    "carbon_emissions_per_revenue": {
        "label": "Carbon Intensity",
        "positive_msg": "Low carbon intensity reflects sustainable operations.",
        "negative_msg": "High carbon intensity is an ESG risk factor.",
        "unit": "tons/₹",
    },
    "compliance_status": {
        "label": "Regulatory Compliance Status",
        "positive_msg": "Compliant status demonstrates regulatory adherence.",
        "negative_msg": "Non-compliant status is a significant risk factor.",
        "unit": "",
    },
    "loan_amount_requested": {
        "label": "Loan Amount",
        "positive_msg": "Loan amount is within acceptable range.",
        "negative_msg": "High loan amount relative to revenue is a risk factor.",
        "unit": "₹",
    },
    "tenure_months": {
        "label": "Loan Tenure",
        "positive_msg": "Loan tenure is appropriate for the amount.",
        "negative_msg": "Extended tenure increases long-term repayment risk.",
        "unit": "months",
    },
    "emi_to_revenue_ratio": {
        "label": "EMI-to-Revenue Ratio",
        "positive_msg": "EMI is well within manageable range vs. revenue.",
        "negative_msg": "High EMI relative to revenue may strain cash flow.",
        "unit": "ratio",
    },
    "sector_type": {
        "label": "Business Sector",
        "positive_msg": "Sector demonstrates strong repayment history.",
        "negative_msg": "Sector carries higher default risk.",
        "unit": "",
    },
}


class RiskExplanationService:
    @staticmethod
    def explain(
        decision: str,
        risk_score: int,
        shap_values: Optional[Dict[str, float]],
        input_features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Produce a human-readable explanation of the ML decision.

        Returns a dict with:
          - summary: one-sentence overall explanation
          - risk_level: "low" | "medium" | "high"
          - factors: list of factor dicts with label, impact, message
          - recommendations: list of actionable improvement suggestions
        """
        risk_level = RiskExplanationService._risk_level(risk_score)
        summary = RiskExplanationService._summary(decision, risk_level)
        factors = RiskExplanationService._factors(shap_values)
        recommendations = RiskExplanationService._recommendations(
            decision, shap_values, input_features or {}
        )

        return {
            "summary": summary,
            "risk_level": risk_level,
            "decision": decision,
            "risk_score": risk_score,
            "factors": factors,
            "recommendations": recommendations,
        }

    @staticmethod
    def _risk_level(risk_score: int) -> str:
        if risk_score >= 700:
            return "low"
        elif risk_score >= 400:
            return "medium"
        return "high"

    @staticmethod
    def _summary(decision: str, risk_level: str) -> str:
        templates = {
            "approved": f"Your loan application has been approved with {risk_level} risk profile.",
            "manual_review": (
                f"Your application requires manual review due to a {risk_level} risk profile. "
                "A loan officer will assess your case shortly."
            ),
            "rejected": (
                f"Your loan application was not approved at this time due to a {risk_level} risk profile. "
                "Please review the factors below and consider reapplying after improvements."
            ),
        }
        return templates.get(decision, "Your application has been processed.")

    @staticmethod
    def _factors(shap_values: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        if not shap_values:
            return []

        factors = []
        for feature, shap_val in sorted(
            shap_values.items(), key=lambda x: abs(x[1]), reverse=True
        ):
            meta = _FEATURE_META.get(feature, {
                "label": feature.replace("_", " ").title(),
                "positive_msg": "Positive influence on decision.",
                "negative_msg": "Negative influence on decision.",
                "unit": "",
            })
            impact = "positive" if shap_val >= 0 else "negative"
            message = meta["positive_msg"] if shap_val >= 0 else meta["negative_msg"]
            factors.append({
                "feature": feature,
                "label": meta["label"],
                "shap_value": round(shap_val, 4),
                "impact": impact,
                "message": message,
            })

        return factors[:8]  # Return top 8 most influential factors

    @staticmethod
    def _recommendations(
        decision: str,
        shap_values: Optional[Dict[str, float]],
        input_features: Dict[str, Any],
    ) -> List[str]:
        recs = []
        if not shap_values:
            return recs

        # Revenue-based recommendations
        if shap_values.get("gst_revenue_3m_avg", 0) < -0.05:
            recs.append(
                "Increase GST-compliant revenue through formal billing channels to improve creditworthiness."
            )
        if shap_values.get("gst_revenue_growth_rate", 0) < -0.05:
            recs.append("Focus on growing revenue over the next 3–6 months before reapplying.")

        # ESG recommendations
        if shap_values.get("renewable_energy_mix", 0) < 0:
            recs.append(
                "Increase renewable energy usage — this directly improves your ESG score and interest rate."
            )
        if shap_values.get("compliance_status", 0) < 0:
            recs.append(
                "Resolve outstanding compliance issues to reach 'compliant' status, which significantly boosts your profile."
            )

        # Loan structure recommendations
        emi_ratio = float(input_features.get("emi_to_revenue_ratio", 0))
        if emi_ratio > 0.5:
            recs.append(
                "Consider requesting a smaller loan amount or longer tenure to reduce the EMI-to-revenue ratio below 0.5."
            )

        if not recs and decision == "approved":
            recs.append("Maintain your current financial and ESG performance to continue qualifying for competitive rates.")

        return recs
