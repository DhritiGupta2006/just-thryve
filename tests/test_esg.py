"""Tests for GET /esg/metrics endpoint."""
import uuid
from types import SimpleNamespace

import pytest

from app.services.auth_service import require_role


def _make_profile(
    renewable_mix_percent: int = 65,
    carbon_emissions_tons=12.4,
    compliance_status: str = "compliant",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_name="SolarFarm Ltd",
        sector="renewable_energy",
        renewable_mix_percent=renewable_mix_percent,
        carbon_emissions_tons=carbon_emissions_tons,
        compliance_status=compliance_status,
    )


class TestGetESGMetrics:
    URL = "/esg/metrics"

    # ------------------------------------------------------------------
    # Success cases
    # ------------------------------------------------------------------

    def test_borrower_gets_metrics_for_own_profile(self, borrower_client, mock_db):
        profile = _make_profile()
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        response = borrower_client.get(self.URL)

        assert response.status_code == 200
        data = response.json()
        assert data["renewable_energy_percent"] == 65.0
        assert data["carbon_intensity"] == 12.4
        assert data["compliance_score"] == 100  # "compliant" maps to 100
        assert "waste_recycled_percent" in data
        assert "social_impact_score" in data

    def test_compliance_pending_maps_to_60(self, borrower_client, mock_db):
        profile = _make_profile(compliance_status="pending")
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        response = borrower_client.get(self.URL)

        assert response.status_code == 200
        assert response.json()["compliance_score"] == 60

    def test_compliance_non_compliant_maps_to_20(self, borrower_client, mock_db):
        profile = _make_profile(compliance_status="non_compliant")
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        response = borrower_client.get(self.URL)

        assert response.status_code == 200
        assert response.json()["compliance_score"] == 20

    def test_none_values_default_to_zero(self, borrower_client, mock_db):
        profile = _make_profile(renewable_mix_percent=0, carbon_emissions_tons=None)
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        response = borrower_client.get(self.URL)

        assert response.status_code == 200
        data = response.json()
        assert data["renewable_energy_percent"] == 0.0
        assert data["carbon_intensity"] == 0.0

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_profile_not_found_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(self.URL)

        assert response.status_code == 404

    def test_lender_cannot_access_esg_metrics(self, lender_client, mock_db):
        response = lender_client.get(self.URL)

        assert response.status_code == 403

    def test_unauthenticated_returns_403(self, client, mock_db):
        response = client.get(self.URL)

        assert response.status_code == 403
