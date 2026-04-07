"""Tests for POST /consent/{id}/revoke endpoint."""
import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest


def _make_consent(user_id, status: str = "granted") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        consent_type="bank_statement",
        status=status,
        metadata_={"artefact_id": str(uuid.uuid4())},
        granted_at=datetime.utcnow(),
        revoked_at=None,
        created_at=datetime.utcnow(),
    )


class TestRevokeConsent:
    def test_borrower_can_revoke_granted_consent(self, borrower_client, mock_db, borrower):
        consent = _make_consent(borrower.id, status="granted")
        mock_db.query.return_value.filter.return_value.first.return_value = consent

        response = borrower_client.post(f"/consent/{consent.id}/revoke")
        assert response.status_code == 200
        data = response.json()
        assert data["consent_id"] == str(consent.id)
        assert data["status"] == "revoked"
        assert data["revoked_at"] is not None

    def test_revoke_already_revoked_returns_400(self, borrower_client, mock_db, borrower):
        consent = _make_consent(borrower.id, status="revoked")
        consent.revoked_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = consent

        response = borrower_client.post(f"/consent/{consent.id}/revoke")
        assert response.status_code == 400

    def test_revoke_nonexistent_consent_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post(f"/consent/{uuid.uuid4()}/revoke")
        assert response.status_code == 404

    def test_revoke_requires_authentication(self, client):
        response = client.post(f"/consent/{uuid.uuid4()}/revoke")
        assert response.status_code in (401, 403)
