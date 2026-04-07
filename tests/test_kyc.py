"""Tests for POST /auth/kyc/verify endpoint."""
import uuid
from types import SimpleNamespace

import pytest


def _make_user(kyc_verified: bool = False, role: str = "borrower") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=f"user_{role}@example.com",
        name="Test User",
        role=role,
        kyc_verified=kyc_verified,
        created_at=None,
    )


class TestKYCVerify:
    URL = "/auth/kyc/verify"

    def test_unverified_user_can_verify_kyc(self, borrower_client, mock_db, borrower):
        # borrower fixture has kyc_verified=False
        borrower.created_at = __import__("datetime").datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "kyc_verified", True)

        response = borrower_client.post(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["kyc_verified"] is True
        assert data["user_id"] == str(borrower.id)

    def test_already_verified_returns_400(self, borrower_client, mock_db, borrower):
        borrower.kyc_verified = True
        borrower.created_at = __import__("datetime").datetime.utcnow()

        response = borrower_client.post(self.URL)
        assert response.status_code == 400

    def test_lender_can_also_verify_kyc(self, lender_client, mock_db, lender):
        lender.kyc_verified = False
        lender.created_at = __import__("datetime").datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "kyc_verified", True)

        response = lender_client.post(self.URL)
        assert response.status_code == 200

    def test_unauthenticated_returns_403(self, client):
        response = client.post(self.URL)
        assert response.status_code in (401, 403)
