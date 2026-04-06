"""Route-level tests for /auth endpoints."""
import uuid
from types import SimpleNamespace

import pytest

from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class TestSignup:
    SIGNUP_URL = "/auth/signup"

    def _payload(self, **overrides):
        base = {
            "email": "new@example.com",
            "password": "securepassword123",
            "name": "Jane Doe",
            "role": "borrower",
        }
        base.update(overrides)
        return base

    def test_signup_borrower_success(self, client, mock_db):
        response = client.post(self.SIGNUP_URL, json=self._payload())
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["role"] == "borrower"
        assert "user_id" in data

    def test_signup_lender_success(self, client, mock_db):
        response = client.post(self.SIGNUP_URL, json=self._payload(role="lender"))
        assert response.status_code == 201
        assert response.json()["role"] == "lender"

    def test_signup_borrower_with_business_profile(self, client, mock_db):
        payload = self._payload(business_name="SolarFarm Ltd", sector="renewable_energy")
        response = client.post(self.SIGNUP_URL, json=payload)
        assert response.status_code == 201
        # Business profile should have been added to session
        assert mock_db.add.call_count >= 2

    def test_signup_duplicate_email_returns_409(self, client, mock_db):
        # Simulate existing user found in DB
        existing = SimpleNamespace(id=uuid.uuid4(), email="existing@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        response = client.post(self.SIGNUP_URL, json=self._payload(email="existing@example.com"))
        assert response.status_code == 409

    def test_signup_invalid_role_returns_400(self, client, mock_db):
        response = client.post(self.SIGNUP_URL, json=self._payload(role="admin"))
        assert response.status_code == 400

    def test_signup_invalid_sector_returns_400(self, client, mock_db):
        payload = self._payload(business_name="BizCo", sector="crypto")
        response = client.post(self.SIGNUP_URL, json=payload)
        assert response.status_code == 400

    def test_signup_invalid_email_returns_422(self, client, mock_db):
        response = client.post(self.SIGNUP_URL, json=self._payload(email="not-an-email"))
        assert response.status_code == 422

    def test_signup_missing_required_fields_returns_422(self, client, mock_db):
        response = client.post(self.SIGNUP_URL, json={"email": "a@b.com"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    LOGIN_URL = "/auth/login"

    def _make_user(self, password: str = "correct_password") -> SimpleNamespace:
        return SimpleNamespace(
            id=uuid.uuid4(),
            email="user@example.com",
            name="Test User",
            role="borrower",
            password_hash=AuthService.hash_password(password),
        )

    def test_login_success(self, client, mock_db):
        user = self._make_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        response = client.post(self.LOGIN_URL, json={"email": user.email, "password": "correct_password"})
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["role"] == "borrower"
        assert data["user_id"] == str(user.id)

    def test_login_wrong_password_returns_401(self, client, mock_db):
        user = self._make_user(password="correct_password")
        mock_db.query.return_value.filter.return_value.first.return_value = user

        response = client.post(self.LOGIN_URL, json={"email": user.email, "password": "wrongpassword"})
        assert response.status_code == 401

    def test_login_unknown_email_returns_401(self, client, mock_db):
        # DB returns nothing
        response = client.post(self.LOGIN_URL, json={"email": "ghost@example.com", "password": "any"})
        assert response.status_code == 401

    def test_login_invalid_email_format_returns_422(self, client, mock_db):
        response = client.post(self.LOGIN_URL, json={"email": "not-valid", "password": "pass"})
        assert response.status_code == 422
