"""Tests for OCEN endpoints: /ocen/network-status, /ocen/discover-lenders, /ocen/broadcast/{loan_id}."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest


def _make_loan(status="submitted", borrower_id=None, amount=Decimal("500000.00")) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=amount,
        purpose="Solar installation",
        tenure_months=12,
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def _make_profile(user_id, sector="renewable_energy") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        sector=sector,
    )


class TestOCENNetworkStatus:
    URL = "/ocen/network-status"

    def test_authenticated_user_can_get_status(self, borrower_client):
        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "protocol_version" in data
        assert data["active_lenders"] > 0
        assert "features" in data

    def test_lender_can_also_get_status(self, lender_client):
        response = lender_client.get(self.URL)
        assert response.status_code == 200

    def test_unauthenticated_returns_403(self, client):
        response = client.get(self.URL)
        assert response.status_code in (401, 403)


class TestOCENDiscoverLenders:
    URL = "/ocen/discover-lenders"

    def test_discover_lenders_returns_list(self, borrower_client):
        response = borrower_client.get(self.URL, params={
            "loan_amount": 500000,
            "sector": "renewable_energy",
            "tenure_months": 12,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_discover_lenders_response_fields(self, borrower_client):
        response = borrower_client.get(self.URL, params={
            "loan_amount": 500000,
            "sector": "renewable_energy",
        })
        assert response.status_code == 200
        lender = response.json()[0]
        assert "lender_id" in lender
        assert "name" in lender
        assert "indicative_rate_pct" in lender
        assert "estimated_emi" in lender
        assert "sector_match" in lender

    def test_invalid_sector_returns_400(self, borrower_client):
        response = borrower_client.get(self.URL, params={
            "loan_amount": 500000,
            "sector": "crypto",
        })
        assert response.status_code == 400

    def test_very_small_loan_may_have_fewer_lenders(self, borrower_client):
        # A very small loan may exclude high-minimum lenders
        response = borrower_client.get(self.URL, params={
            "loan_amount": 5000,
            "sector": "agriculture",
        })
        assert response.status_code == 200
        data = response.json()
        # Result is a list (possibly empty for very small amounts)
        assert isinstance(data, list)

    def test_unauthenticated_returns_403(self, client):
        response = client.get(self.URL, params={"loan_amount": 500000})
        assert response.status_code in (401, 403)


class TestOCENBroadcast:
    def test_borrower_can_broadcast_submitted_loan(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="submitted", borrower_id=borrower.id)
        profile = _make_profile(borrower.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, profile]

        response = borrower_client.post(f"/ocen/broadcast/{loan.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["loan_id"] == str(loan.id)
        assert data["status"] == "broadcasted"
        assert data["notified_lender_count"] >= 0
        assert "broadcast_id" in data
        assert "response_deadline" in data

    def test_broadcast_offers_received_loan(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="offers_received", borrower_id=borrower.id)
        profile = _make_profile(borrower.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, profile]

        response = borrower_client.post(f"/ocen/broadcast/{loan.id}")
        assert response.status_code == 200

    def test_broadcast_wrong_status_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="accepted", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(f"/ocen/broadcast/{loan.id}")
        assert response.status_code == 400

    def test_broadcast_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post(f"/ocen/broadcast/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_borrower_cannot_broadcast_other_users_loan(self, borrower_client, mock_db):
        loan = _make_loan(status="submitted")  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(f"/ocen/broadcast/{loan.id}")
        assert response.status_code == 403

    def test_lender_can_view_broadcast_for_any_loan(self, lender_client, mock_db):
        loan = _make_loan(status="submitted")
        profile = _make_profile(loan.borrower_id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, profile]

        response = lender_client.post(f"/ocen/broadcast/{loan.id}")
        # Lender is not the borrower, but broadcast allows any authenticated user
        # who has access to the loan. Since lenders can see all loans:
        assert response.status_code == 200
