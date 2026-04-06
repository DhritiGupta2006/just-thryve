"""Tests for the ML service predictions and audit log creation during loan submission."""
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.ml_service import MLService, SECTOR_MAP, COMPLIANCE_MAP, FEATURE_NAMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loan(borrower_id=None, status: str = "created") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=Decimal("500000.00"),
        purpose="Solar installation",
        tenure_months=12,
        status=status,
        risk_score=None,
        ml_decision=None,
        created_at=datetime.utcnow(),
        submitted_at=None,
        disbursed_at=None,
        closed_at=None,
    )


def _make_profile(user_id, sector="renewable_energy", compliance="compliant") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        business_name="GreenBiz Ltd",
        sector=sector,
        avg_gst_revenue_3m=Decimal("500000.00"),
        renewable_mix_percent=80,
        carbon_emissions_tons=Decimal("5.0000"),
        compliance_status=compliance,
    )


# ---------------------------------------------------------------------------
# ML prediction + audit log integration (via /loans/{id}/submit)
# ---------------------------------------------------------------------------

class TestMLAuditLogCreation:
    def test_submit_creates_audit_log(self, borrower_client, mock_db, borrower):
        from app.main import app
        from app.routers.loans import get_ml_service

        loan = _make_loan(borrower_id=borrower.id)
        profile = _make_profile(borrower.id)

        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, profile]

        mock_ml = MagicMock()
        mock_ml.predict.return_value = {
            "decision": "approved",
            "risk_score": 800,
            "confidence": 0.90,
            "shap_values": {"gst_revenue_3m_avg": 0.25, "renewable_energy_mix": 0.20},
            "model_version": "1.0.0",
            "input_features": {"gst_revenue_3m_avg": 500000.0},
        }

        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        try:
            response = borrower_client.post(f"/loans/{loan.id}/submit")
        finally:
            app.dependency_overrides.pop(get_ml_service, None)

        assert response.status_code == 200
        # Verify that db.add was called at least once for the MLAuditLog
        assert mock_db.add.call_count >= 1

    def test_submit_records_ml_decision_and_risk_score(self, borrower_client, mock_db, borrower):
        from app.main import app
        from app.routers.loans import get_ml_service

        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, None]

        mock_ml = MagicMock()
        mock_ml.predict.return_value = {
            "decision": "rejected",
            "risk_score": 200,
            "confidence": 0.92,
            "shap_values": {},
            "model_version": "heuristic-1.0",
            "input_features": {},
        }

        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        try:
            response = borrower_client.post(f"/loans/{loan.id}/submit")
        finally:
            app.dependency_overrides.pop(get_ml_service, None)

        assert response.status_code == 200
        data = response.json()
        assert data["ml_decision"] == "rejected"
        assert data["risk_score"] == 200

    def test_submit_manual_review_decision(self, borrower_client, mock_db, borrower):
        from app.main import app
        from app.routers.loans import get_ml_service

        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, None]

        mock_ml = MagicMock()
        mock_ml.predict.return_value = {
            "decision": "manual_review",
            "risk_score": 520,
            "confidence": 0.55,
            "shap_values": {},
            "model_version": "1.0.0",
            "input_features": {},
        }

        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        try:
            response = borrower_client.post(f"/loans/{loan.id}/submit")
        finally:
            app.dependency_overrides.pop(get_ml_service, None)

        assert response.status_code == 200
        data = response.json()
        assert data["ml_decision"] == "manual_review"
        assert data["risk_score"] == 520


# ---------------------------------------------------------------------------
# MLService unit tests — feature engineering
# ---------------------------------------------------------------------------

class TestMLServiceFeatureEngineering:
    """Tests for feature vector construction; does not require a real model."""

    def setup_method(self):
        # Instantiate with a non-existent path → uses heuristic fallback
        self.svc = MLService(model_path="/tmp/no_model_here.pkl")

    def test_feature_vector_shape(self):
        features = {
            "gst_revenue_3m_avg": 300_000,
            "gst_revenue_growth_rate": 5.0,
            "gst_revenue_volatility": 10_000,
            "renewable_energy_mix": 60,
            "carbon_emissions_per_revenue": 0.02,
            "compliance_status": "compliant",
            "loan_amount_requested": 500_000,
            "tenure_months": 12,
            "sector": "renewable_energy",
        }
        vec = self.svc._build_feature_vector(features)
        assert vec.shape == (len(FEATURE_NAMES),)

    def test_sector_encoding_renewable(self):
        features = {
            "gst_revenue_3m_avg": 100_000,
            "gst_revenue_growth_rate": 0,
            "gst_revenue_volatility": 0,
            "renewable_energy_mix": 50,
            "carbon_emissions_per_revenue": 0,
            "compliance_status": "compliant",
            "loan_amount_requested": 100_000,
            "tenure_months": 12,
            "sector": "renewable_energy",
        }
        vec = self.svc._build_feature_vector(features)
        # sector_type is the last feature (index 9)
        assert vec[9] == SECTOR_MAP["renewable_energy"]

    def test_compliance_encoding_non_compliant(self):
        features = {
            "gst_revenue_3m_avg": 100_000,
            "gst_revenue_growth_rate": 0,
            "gst_revenue_volatility": 0,
            "renewable_energy_mix": 10,
            "carbon_emissions_per_revenue": 0,
            "compliance_status": "non_compliant",
            "loan_amount_requested": 100_000,
            "tenure_months": 12,
            "sector": "agriculture",
        }
        vec = self.svc._build_feature_vector(features)
        # compliance is feature index 5
        assert vec[5] == COMPLIANCE_MAP["non_compliant"]

    def test_emi_ratio_defaults_to_one_when_revenue_is_zero(self):
        features = {
            "gst_revenue_3m_avg": 0,
            "gst_revenue_growth_rate": 0,
            "gst_revenue_volatility": 0,
            "renewable_energy_mix": 0,
            "carbon_emissions_per_revenue": 0,
            "compliance_status": "pending",
            "loan_amount_requested": 200_000,
            "tenure_months": 12,
            "sector": "commerce",
        }
        vec = self.svc._build_feature_vector(features)
        # emi_to_revenue_ratio is index 8; should default to 1.0 when revenue=0
        assert vec[8] == 1.0


# ---------------------------------------------------------------------------
# MLService heuristic predict — audit result keys
# ---------------------------------------------------------------------------

class TestMLServiceAuditOutputKeys:
    def setup_method(self):
        self.svc = MLService(model_path="/tmp/no_model_here.pkl")

    def test_predict_output_contains_all_audit_keys(self):
        features = {
            "gst_revenue_3m_avg": 400_000,
            "gst_revenue_growth_rate": 12,
            "gst_revenue_volatility": 20_000,
            "renewable_energy_mix": 70,
            "carbon_emissions_per_revenue": 0.01,
            "compliance_status": "compliant",
            "loan_amount_requested": 300_000,
            "tenure_months": 12,
            "sector": "renewable_energy",
        }
        result = self.svc.predict(features)
        required_keys = {"decision", "risk_score", "confidence", "model_version", "input_features"}
        assert required_keys.issubset(result.keys())

    def test_predict_decision_is_valid_value(self):
        features = {
            "gst_revenue_3m_avg": 100_000,
            "gst_revenue_growth_rate": 5,
            "gst_revenue_volatility": 0,
            "renewable_energy_mix": 30,
            "carbon_emissions_per_revenue": 0.05,
            "compliance_status": "pending",
            "loan_amount_requested": 500_000,
            "tenure_months": 24,
            "sector": "agriculture",
        }
        result = self.svc.predict(features)
        assert result["decision"] in ("approved", "manual_review", "rejected")

    def test_predict_risk_score_bounds(self):
        features = {
            "gst_revenue_3m_avg": 200_000,
            "gst_revenue_growth_rate": 0,
            "gst_revenue_volatility": 0,
            "renewable_energy_mix": 40,
            "carbon_emissions_per_revenue": 0.03,
            "compliance_status": "compliant",
            "loan_amount_requested": 150_000,
            "tenure_months": 18,
            "sector": "commerce",
        }
        result = self.svc.predict(features)
        assert 0 <= result["risk_score"] <= 1000

    def test_predict_confidence_bounds(self):
        features = {
            "gst_revenue_3m_avg": 600_000,
            "gst_revenue_growth_rate": 20,
            "gst_revenue_volatility": 5000,
            "renewable_energy_mix": 90,
            "carbon_emissions_per_revenue": 0.005,
            "compliance_status": "compliant",
            "loan_amount_requested": 200_000,
            "tenure_months": 6,
            "sector": "renewable_energy",
        }
        result = self.svc.predict(features)
        assert 0.0 <= result["confidence"] <= 1.0
