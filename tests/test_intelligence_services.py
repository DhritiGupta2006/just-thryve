"""Unit tests for DynamicRateService, RiskExplanationService, LoanComparisonService."""
import pytest

from app.services.dynamic_rate_service import DynamicRateService
from app.services.risk_explanation_service import RiskExplanationService
from app.services.loan_comparison_service import LoanComparisonService


# ---------------------------------------------------------------------------
# DynamicRateService
# ---------------------------------------------------------------------------

class TestDynamicRateService:
    def test_high_risk_score_gives_lower_rate(self):
        high_rate = DynamicRateService.compute_rate(risk_score=200)
        low_rate = DynamicRateService.compute_rate(risk_score=900)
        assert low_rate < high_rate

    def test_rate_is_within_bounds(self):
        for score in [0, 250, 500, 750, 1000]:
            rate = DynamicRateService.compute_rate(risk_score=score)
            assert 6.0 <= rate <= 24.0, f"Rate {rate} out of bounds for score {score}"

    def test_compliant_esg_lowers_rate(self):
        rate_no_esg = DynamicRateService.compute_rate(
            risk_score=600,
            compliance_status="pending",
            renewable_mix_percent=0,
        )
        rate_with_esg = DynamicRateService.compute_rate(
            risk_score=600,
            compliance_status="compliant",
            renewable_mix_percent=80,
            waste_recycled_percent=50,
            social_impact_score=70,
        )
        assert rate_with_esg < rate_no_esg

    def test_non_compliant_penalised(self):
        compliant_rate = DynamicRateService.compute_rate(
            risk_score=600, compliance_status="compliant"
        )
        non_compliant_rate = DynamicRateService.compute_rate(
            risk_score=600, compliance_status="non_compliant"
        )
        assert non_compliant_rate > compliant_rate

    def test_rate_breakdown_keys(self):
        breakdown = DynamicRateService.rate_breakdown(risk_score=500)
        assert "base_rate" in breakdown
        assert "risk_spread" in breakdown
        assert "esg_discount" in breakdown
        assert "final_rate" in breakdown

    def test_breakdown_final_rate_matches_compute_rate(self):
        kwargs = dict(
            risk_score=600,
            renewable_mix_percent=40,
            compliance_status="compliant",
        )
        rate = DynamicRateService.compute_rate(**kwargs)
        breakdown = DynamicRateService.rate_breakdown(**kwargs)
        assert abs(rate - breakdown["final_rate"]) < 0.0001


# ---------------------------------------------------------------------------
# RiskExplanationService
# ---------------------------------------------------------------------------

class TestRiskExplanationService:
    def test_explain_returns_all_required_keys(self):
        result = RiskExplanationService.explain(
            decision="approved",
            risk_score=750,
            shap_values={"gst_revenue_3m_avg": 0.25, "renewable_energy_mix": 0.20},
        )
        assert "summary" in result
        assert "risk_level" in result
        assert "decision" in result
        assert "risk_score" in result
        assert "factors" in result
        assert "recommendations" in result

    def test_high_score_is_low_risk(self):
        result = RiskExplanationService.explain(
            decision="approved", risk_score=800, shap_values=None
        )
        assert result["risk_level"] == "low"

    def test_medium_score_is_medium_risk(self):
        result = RiskExplanationService.explain(
            decision="manual_review", risk_score=500, shap_values=None
        )
        assert result["risk_level"] == "medium"

    def test_low_score_is_high_risk(self):
        result = RiskExplanationService.explain(
            decision="rejected", risk_score=300, shap_values=None
        )
        assert result["risk_level"] == "high"

    def test_factors_sorted_by_magnitude(self):
        shap = {"a": 0.1, "b": -0.5, "c": 0.3}
        result = RiskExplanationService.explain(
            decision="approved", risk_score=600, shap_values=shap
        )
        magnitudes = [abs(f["shap_value"]) for f in result["factors"]]
        assert magnitudes == sorted(magnitudes, reverse=True)

    def test_no_shap_values_returns_empty_factors(self):
        result = RiskExplanationService.explain(
            decision="approved", risk_score=700, shap_values=None
        )
        assert result["factors"] == []

    def test_positive_shap_is_positive_impact(self):
        result = RiskExplanationService.explain(
            decision="approved",
            risk_score=750,
            shap_values={"gst_revenue_3m_avg": 0.3},
        )
        factor = result["factors"][0]
        assert factor["impact"] == "positive"

    def test_negative_shap_is_negative_impact(self):
        result = RiskExplanationService.explain(
            decision="rejected",
            risk_score=200,
            shap_values={"compliance_status": -0.4},
        )
        factor = result["factors"][0]
        assert factor["impact"] == "negative"


# ---------------------------------------------------------------------------
# LoanComparisonService
# ---------------------------------------------------------------------------

class TestLoanComparisonService:
    def _offer(self, offer_id, rate, amount=500000, tenure=12, status="pending"):
        from app.services.emi_service import EMIService
        emi = EMIService.calculate_emi(amount, rate, tenure)
        return {
            "offer_id": str(offer_id),
            "lender_id": "LENDER-001",
            "offered_amount": amount,
            "interest_rate": rate,
            "tenure_months": tenure,
            "emi_amount": emi,
            "status": status,
        }

    def test_empty_offers_returns_empty_comparisons(self):
        result = LoanComparisonService.compare_offers([])
        assert result["comparisons"] == []
        assert result["recommended_offer_id"] is None

    def test_lower_rate_offer_is_recommended(self):
        import uuid
        id1, id2 = str(uuid.uuid4()), str(uuid.uuid4())
        offers = [self._offer(id1, 14.0), self._offer(id2, 10.0)]
        result = LoanComparisonService.compare_offers(offers)
        assert result["recommended_offer_id"] == id2

    def test_comparisons_include_total_cost(self):
        import uuid
        result = LoanComparisonService.compare_offers([self._offer(str(uuid.uuid4()), 12.0)])
        c = result["comparisons"][0]
        assert "total_payment" in c
        assert "total_interest_paid" in c
        assert c["total_payment"] > c["total_interest_paid"]

    def test_early_repayment_summary_structure(self):
        result = LoanComparisonService.early_repayment_summary(
            outstanding_principal=300000.0,
            annual_rate_percent=12.0,
            remaining_months=10,
            prepayment_amount=100000.0,
            prepayment_penalty_percent=2.0,
        )
        assert "outstanding_principal" in result
        assert "prepayment_amount" in result
        assert "prepayment_penalty" in result
        assert "estimated_savings" in result
        assert "fully_repaid" in result
        assert result["prepayment_penalty"] == pytest.approx(2000.0, abs=0.01)

    def test_full_prepayment_marks_fully_repaid(self):
        result = LoanComparisonService.early_repayment_summary(
            outstanding_principal=100000.0,
            annual_rate_percent=12.0,
            remaining_months=6,
            prepayment_amount=200000.0,  # more than outstanding
        )
        assert result["fully_repaid"] is True

    def test_estimated_savings_non_negative(self):
        result = LoanComparisonService.early_repayment_summary(
            outstanding_principal=500000.0,
            annual_rate_percent=12.0,
            remaining_months=24,
            prepayment_amount=100000.0,
        )
        assert result["estimated_savings"] >= 0


# ---------------------------------------------------------------------------
# OCENSimulationService
# ---------------------------------------------------------------------------

class TestOCENSimulationService:
    def setup_method(self):
        from app.services.ocen_simulation_service import OCENSimulationService
        self.svc = OCENSimulationService

    def test_network_status_keys(self):
        status = self.svc.network_status()
        assert status["status"] == "operational"
        assert "protocol_version" in status
        assert "registered_lenders" in status
        assert "active_lenders" in status

    def test_discover_lenders_returns_list(self):
        lenders = self.svc.discover_lenders(500000, "renewable_energy", 12)
        assert isinstance(lenders, list)
        assert len(lenders) > 0

    def test_discover_lenders_sector_match_flag(self):
        lenders = self.svc.discover_lenders(500000, "renewable_energy", 12)
        # At least one lender should match renewable_energy
        matches = [l for l in lenders if l["sector_match"]]
        assert len(matches) > 0

    def test_discover_lenders_sorted_by_rate(self):
        lenders = self.svc.discover_lenders(500000, "commerce", 12)
        rates = [l["indicative_rate_pct"] for l in lenders]
        # Sector-match lenders appear first, within each group sorted by rate
        # Simply verify no lender with a lower rate appears after a higher-rate lender
        # of the same sector_match status
        for match_val in (True, False):
            group = [l["indicative_rate_pct"] for l in lenders if l["sector_match"] == match_val]
            assert group == sorted(group)

    def test_broadcast_returns_required_fields(self):
        result = self.svc.broadcast_loan_request("loan-123", 500000, "renewable_energy")
        assert "broadcast_id" in result
        assert result["loan_id"] == "loan-123"
        assert "notified_lender_count" in result
        assert "response_deadline" in result
        assert result["status"] == "broadcasted"
