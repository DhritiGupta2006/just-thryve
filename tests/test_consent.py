"""Route-level tests for /consent endpoints."""
import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loan(borrower_id=None, status: str = "submitted") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        status=status,
    )


def _make_consent(user_id, consent_type: str = "bank_statement", status: str = "granted") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        consent_type=consent_type,
        status=status,
        redirect_url=None,
        metadata_={"artefact_id": str(uuid.uuid4())},
        granted_at=datetime.utcnow(),
        revoked_at=None,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# POST /consent/grant
# ---------------------------------------------------------------------------

class TestGrantConsent:
    URL = "/consent/grant"

    def _payload(self, loan_id, consent_types=None):
        return {
            "loan_id": str(loan_id),
            "consent_types": consent_types or ["bank_statement", "gst_data"],
        }

    def test_grant_consent_success(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(self.URL, json=self._payload(loan.id))
        assert response.status_code == 201
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["consent_type"] == "bank_statement"
        assert data[0]["status"] == "granted"
        assert "consent_id" in data[0]
        assert "redirect_url" in data[0]

    def test_grant_single_consent_type(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(
            self.URL, json=self._payload(loan.id, ["carbon_audit"])
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["consent_type"] == "carbon_audit"

    def test_grant_all_consent_types(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        all_types = ["bank_statement", "gst_data", "energy_usage", "carbon_audit"]
        response = borrower_client.post(
            self.URL, json=self._payload(loan.id, all_types)
        )
        assert response.status_code == 201
        assert len(response.json()) == 4

    def test_grant_consent_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post(
            self.URL, json=self._payload(uuid.uuid4())
        )
        assert response.status_code == 404

    def test_grant_consent_invalid_type_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(
            self.URL,
            json=self._payload(loan.id, ["invalid_consent_type"]),
        )
        assert response.status_code == 400

    def test_grant_consent_requires_authentication(self, client, mock_db):
        response = client.post(
            self.URL,
            json=self._payload(uuid.uuid4()),
        )
        # Unauthenticated client has no current_user override → 403 from bearer
        assert response.status_code in (401, 403)

    def test_grant_consent_artefact_in_response(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(
            self.URL, json=self._payload(loan.id, ["energy_usage"])
        )
        assert response.status_code == 201
        item = response.json()[0]
        assert "artefact" in item
        assert item["artefact"] is not None


# ---------------------------------------------------------------------------
# GET /consent/{consent_id}/status
# ---------------------------------------------------------------------------

class TestGetConsentStatus:
    def test_get_own_consent_status(self, borrower_client, mock_db, borrower):
        consent = _make_consent(borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = consent

        response = borrower_client.get(f"/consent/{consent.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["consent_id"] == str(consent.id)
        assert data["status"] == "granted"
        assert data["consent_type"] == "bank_statement"

    def test_get_nonexistent_consent_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(f"/consent/{uuid.uuid4()}/status")
        assert response.status_code == 404

    def test_get_consent_status_unauthenticated(self, client, mock_db):
        response = client.get(f"/consent/{uuid.uuid4()}/status")
        assert response.status_code in (401, 403)

    def test_get_revoked_consent_status(self, borrower_client, mock_db, borrower):
        consent = _make_consent(borrower.id, status="revoked")
        consent.revoked_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = consent

        response = borrower_client.get(f"/consent/{consent.id}/status")
        assert response.status_code == 200
        assert response.json()["status"] == "revoked"
