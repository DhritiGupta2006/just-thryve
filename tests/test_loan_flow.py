"""Route-level tests for the loan lifecycle endpoints."""
import uuid
from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loan(status: str = "created", **kwargs) -> SimpleNamespace:
    loan_id = uuid.uuid4()
    return SimpleNamespace(
        id=loan_id,
        borrower_id=kwargs.get("borrower_id", uuid.uuid4()),
        amount_requested=Decimal("500000.00"),
        purpose="Solar panel installation",
        tenure_months=12,
        status=status,
        approved_amount=kwargs.get("approved_amount"),
        approved_rate=kwargs.get("approved_rate"),
        emi_amount=kwargs.get("emi_amount"),
        risk_score=kwargs.get("risk_score"),
        ml_decision=kwargs.get("ml_decision"),
        created_at=datetime.utcnow(),
        submitted_at=kwargs.get("submitted_at"),
        disbursed_at=kwargs.get("disbursed_at"),
        closed_at=kwargs.get("closed_at"),
    )


def _make_offer(loan_id, lender_id, status: str = "pending") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        lender_id=lender_id,
        interest_rate=Decimal("12.0000"),
        offered_amount=Decimal("500000.00"),
        tenure_months=12,
        emi_amount=Decimal("44424.40"),
        status=status,
        accepted_at=None,
        expires_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# POST /loans/apply
# ---------------------------------------------------------------------------

class TestApplyLoan:
    URL = "/loans/apply"
    PAYLOAD = {
        "amount_requested": "500000.00",
        "purpose": "Solar panel installation",
        "tenure_months": 12,
    }

    def test_borrower_can_apply(self, borrower_client):
        response = borrower_client.post(self.URL, json=self.PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert "loan_id" in data
        assert data["status"] == "created"

    def test_lender_cannot_apply(self, lender_client):
        response = lender_client.post(self.URL, json=self.PAYLOAD)
        assert response.status_code == 403

    def test_missing_fields_returns_422(self, borrower_client):
        response = borrower_client.post(self.URL, json={"purpose": "test"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /loans/{loan_id}/submit
# ---------------------------------------------------------------------------

class TestSubmitLoan:
    def test_submit_created_loan(self, borrower_client, mock_db, borrower):
        from app.main import app
        from app.routers.loans import get_ml_service

        loan = _make_loan(status="created", borrower_id=borrower.id)

        # First query returns the loan; second query (BusinessProfile) returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [loan, None]

        mock_ml = MagicMock()
        mock_ml.predict.return_value = {
            "decision": "approved",
            "risk_score": 750,
            "confidence": 0.85,
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
        assert data["ml_decision"] == "approved"
        assert data["risk_score"] == 750

    def test_submit_non_created_loan_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="submitted", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(f"/loans/{loan.id}/submit")

        assert response.status_code == 400

    def test_submit_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post(f"/loans/{uuid.uuid4()}/submit")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /loans/{loan_id}
# ---------------------------------------------------------------------------

class TestGetLoan:
    def test_borrower_can_get_own_loan(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="submitted", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/loans/{loan.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "submitted"

    def test_borrower_cannot_get_other_loan(self, borrower_client, mock_db):
        loan = _make_loan(status="submitted")
        # borrower_id differs from the authenticated borrower
        loan.borrower_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/loans/{loan.id}")
        assert response.status_code == 403

    def test_lender_can_get_any_loan(self, lender_client, mock_db):
        loan = _make_loan(status="submitted")
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = lender_client.get(f"/loans/{loan.id}")
        assert response.status_code == 200

    def test_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = borrower_client.get(f"/loans/{uuid.uuid4()}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /offers  (create offer as lender)
# ---------------------------------------------------------------------------

class TestCreateOffer:
    URL = "/offers"

    def test_lender_can_create_offer(self, lender_client, mock_db, lender):
        loan = _make_loan(status="submitted")
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        payload = {
            "loan_id": str(loan.id),
            "interest_rate": "12.0",
            "offered_amount": "500000.00",
            "tenure_months": 12,
        }
        response = lender_client.post(self.URL, json=payload)
        assert response.status_code == 201
        assert "offer_id" in response.json()

    def test_borrower_cannot_create_offer(self, borrower_client, mock_db):
        loan = _make_loan(status="submitted")
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        payload = {
            "loan_id": str(loan.id),
            "interest_rate": "12.0",
            "offered_amount": "500000.00",
            "tenure_months": 12,
        }
        response = borrower_client.post(self.URL, json=payload)
        assert response.status_code == 403

    def test_offer_on_nonexistent_loan_returns_404(self, lender_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        payload = {
            "loan_id": str(uuid.uuid4()),
            "interest_rate": "12.0",
            "offered_amount": "500000.00",
            "tenure_months": 12,
        }
        response = lender_client.post(self.URL, json=payload)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_root_health(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
