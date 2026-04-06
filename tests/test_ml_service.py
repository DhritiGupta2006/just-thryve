"""Unit tests for MLService — no database required."""
import pytest

from app.services.ml_service import MLService, SECTOR_MAP, COMPLIANCE_MAP


@pytest.fixture()
def ml_service(tmp_path) -> MLService:
    """MLService instance with no model file → heuristic fallback."""
    # Reset class-level cached model so a previous test's loaded model doesn't bleed in
    MLService._model = None
    MLService._explainer = None
    return MLService(model_path=str(tmp_path / "nonexistent_model.pkl"))


def _base_features(**overrides) -> dict:
    defaults = {
        "gst_revenue_3m_avg": 500_000,
        "gst_revenue_growth_rate": 15.0,
        "gst_revenue_volatility": 10_000,
        "renewable_energy_mix": 60,
        "carbon_emissions_per_revenue": 0.02,
        "compliance_status": "compliant",
        "loan_amount_requested": 300_000,
        "tenure_months": 12,
        "sector": "renewable_energy",
    }
    defaults.update(overrides)
    return defaults


class TestHeuristicPredict:
    def test_approved_for_strong_profile(self, ml_service):
        features = _base_features(
            gst_revenue_3m_avg=1_000_000,
            loan_amount_requested=200_000,
            renewable_energy_mix=80,
            compliance_status="compliant",
            gst_revenue_growth_rate=20,
        )
        result = ml_service.predict(features)
        assert result["decision"] == "approved"
        assert 0 <= result["risk_score"] <= 1000
        assert result["model_version"] == "heuristic-1.0"

    def test_rejected_for_weak_profile(self, ml_service):
        features = _base_features(
            gst_revenue_3m_avg=10_000,
            loan_amount_requested=5_000_000,
            renewable_energy_mix=0,
            compliance_status="non_compliant",
            gst_revenue_growth_rate=-20,
        )
        result = ml_service.predict(features)
        assert result["decision"] == "rejected"

    def test_manual_review_for_borderline_profile(self, ml_service):
        features = _base_features(
            gst_revenue_3m_avg=300_000,
            loan_amount_requested=1_000_000,
            renewable_energy_mix=30,
            compliance_status="pending",
            gst_revenue_growth_rate=5,
        )
        result = ml_service.predict(features)
        assert result["decision"] in ("manual_review", "approved", "rejected")

    def test_result_has_required_keys(self, ml_service):
        result = ml_service.predict(_base_features())
        for key in ("decision", "risk_score", "confidence", "shap_values", "model_version", "input_features"):
            assert key in result

    def test_confidence_in_range(self, ml_service):
        result = ml_service.predict(_base_features())
        assert 0.0 <= result["confidence"] <= 1.0

    def test_risk_score_in_range(self, ml_service):
        result = ml_service.predict(_base_features())
        assert 0 <= result["risk_score"] <= 1000


class TestFeatureVector:
    def test_sector_mapping(self, ml_service):
        for sector, expected_idx in SECTOR_MAP.items():
            vec = ml_service._build_feature_vector(_base_features(sector=sector))
            assert int(vec[9]) == expected_idx

    def test_compliance_mapping(self, ml_service):
        for status, expected_idx in COMPLIANCE_MAP.items():
            vec = ml_service._build_feature_vector(_base_features(compliance_status=status))
            assert int(vec[5]) == expected_idx

    def test_unknown_sector_defaults_to_commerce(self, ml_service):
        vec = ml_service._build_feature_vector(_base_features(sector="unknown_sector"))
        assert int(vec[9]) == SECTOR_MAP["commerce"]

    def test_feature_vector_length(self, ml_service):
        vec = ml_service._build_feature_vector(_base_features())
        assert len(vec) == 10

    def test_emi_ratio_zero_revenue_defaults_to_one(self, ml_service):
        features = _base_features(gst_revenue_3m_avg=0, loan_amount_requested=100_000)
        vec = ml_service._build_feature_vector(features)
        # emi_ratio index is 8; when avg_rev == 0, ratio clamps to 1.0
        assert vec[8] == pytest.approx(1.0)
