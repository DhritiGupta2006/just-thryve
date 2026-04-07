"""Tests for GET /dashboard/borrower and GET /dashboard/lender endpoints."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


def _make_loan(
    borrower_id=None,
    status: str = "disbursed",
    amount_requested=Decimal("500000.00"),
    approved_amount=Decimal("500000.00"),
    approved_rate=Decimal("12.0000"),
    emi_amount=Decimal("44424.40"),
    risk_score: int = 750,
    ml_decision: str = "approved",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=amount_requested,
        approved_amount=approved_amount,
        approved_rate=approved_rate,
        emi_amount=emi_amount,
        risk_score=risk_score,
        ml_decision=ml_decision,
        status=status,
        created_at=datetime(2026, 1, 1),
        submitted_at=datetime(2026, 1, 2),
        disbursed_at=datetime(2026, 1, 3),
        closed_at=None,
    )


def _make_offer(
    lender_id=None,
    loan_id=None,
    status: str = "accepted",
    offered_amount=Decimal("500000.00"),
    interest_rate=Decimal("12.0000"),
    tenure_months: int = 12,
    emi_amount=Decimal("44424.40"),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id or uuid.uuid4(),
        lender_id=lender_id or uuid.uuid4(),
        offered_amount=offered_amount,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        emi_amount=emi_amount,
        status=status,
        accepted_at=datetime(2026, 1, 5),
        expires_at=datetime(2026, 2, 5),
        created_at=datetime(2026, 1, 4),
    )


def _make_repayment(loan_id=None, status: str = "paid", emi_amount=Decimal("44424.40")) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id or uuid.uuid4(),
        installment_number=1,
        due_date=date(2026, 2, 1),
        principal_amount=Decimal("40000.00"),
        interest_amount=Decimal("4424.40"),
        emi_amount=emi_amount,
        status=status,
        paid_on=datetime(2026, 2, 1) if status == "paid" else None,
    )


# ---------------------------------------------------------------------------
# Borrower dashboard
# ---------------------------------------------------------------------------

class TestBorrowerDashboard:
    URL = "/dashboard/borrower"

    def _setup_db(self, mock_db, loans, paid_schedules, next_emi=None):
        """Wire up mock_db to return the given fixture data in query order."""
        # query().filter().order_by().all() → loans
        # query().filter().all() → paid_schedules  (two filter().all() calls needed)
        # query().filter().order_by().first() → next_emi
        call_results = []

        class _QueryBuilder:
            def __init__(self_inner):
                self_inner._calls = 0

            def filter(self_inner, *args):
                return self_inner

            def order_by(self_inner, *args):
                return self_inner

            def limit(self_inner, *args):
                return self_inner

            def all(self_inner):
                self_inner._calls += 1
                if self_inner._calls == 1:
                    return loans
                return paid_schedules

            def first(self_inner):
                return next_emi

        mock_db.query.return_value = _QueryBuilder()

    def test_returns_200_with_empty_data(self, borrower_client, mock_db):
        # No loans: all().return_value = [] by default in conftest
        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["loan_count"] == 0
        assert data["total_requested"] == 0.0
        assert data["total_repaid"] == 0.0
        assert data["loans"] == []

    def test_loan_count_and_totals(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        paid = _make_repayment(loan_id=loan.id, status="paid")
        self._setup_db(mock_db, [loan], [paid])

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["loan_count"] == 1
        assert data["active_loan_count"] == 1
        assert data["total_requested"] == 500000.0
        assert data["total_approved"] == 500000.0
        assert abs(data["total_repaid"] - 44424.40) < 0.01

    def test_next_emi_present_when_pending_schedule(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        pending = _make_repayment(loan_id=loan.id, status="pending")
        self._setup_db(mock_db, [loan], [], next_emi=pending)

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["next_emi_date"] == "2026-02-01"
        assert abs(data["next_emi_amount"] - 44424.40) < 0.01

    def test_loan_summary_fields_present(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        self._setup_db(mock_db, [loan], [])

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        summary = response.json()["loans"][0]
        assert "loan_id" in summary
        assert summary["status"] == "disbursed"
        assert summary["ml_decision"] == "approved"
        assert summary["risk_score"] == 750

    def test_lender_cannot_access_borrower_dashboard(self, lender_client, mock_db):
        response = lender_client.get(self.URL)
        assert response.status_code == 403

    def test_unauthenticated_returns_403(self, client, mock_db):
        response = client.get(self.URL)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Lender dashboard
# ---------------------------------------------------------------------------

class TestLenderDashboard:
    URL = "/dashboard/lender"

    def _setup_db(self, mock_db, offers):
        class _QueryBuilder:
            def filter(self_inner, *args):
                return self_inner

            def order_by(self_inner, *args):
                return self_inner

            def limit(self_inner, *args):
                return self_inner

            def all(self_inner):
                return offers

            def first(self_inner):
                return None

        mock_db.query.return_value = _QueryBuilder()

    def test_returns_200_with_empty_data(self, lender_client, mock_db):
        response = lender_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["offer_count"] == 0
        assert data["accepted_offer_count"] == 0
        assert data["portfolio_value"] == 0.0
        assert data["offers"] == []

    def test_portfolio_value_sums_accepted_offers(self, lender_client, mock_db, lender):
        acc = _make_offer(lender_id=lender.id, status="accepted")
        rej = _make_offer(lender_id=lender.id, status="rejected")
        self._setup_db(mock_db, [acc, rej])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        assert data["offer_count"] == 2
        assert data["accepted_offer_count"] == 1
        assert data["portfolio_value"] == 500000.0

    def test_average_interest_rate_computed(self, lender_client, mock_db, lender):
        o1 = _make_offer(lender_id=lender.id, interest_rate=Decimal("10.0000"))
        o2 = _make_offer(lender_id=lender.id, interest_rate=Decimal("12.0000"))
        self._setup_db(mock_db, [o1, o2])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        assert abs(response.json()["average_interest_rate"] - 11.0) < 0.01

    def test_offer_summary_fields_present(self, lender_client, mock_db, lender):
        offer = _make_offer(lender_id=lender.id)
        self._setup_db(mock_db, [offer])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        summary = response.json()["offers"][0]
        assert "offer_id" in summary
        assert "loan_id" in summary
        assert summary["status"] == "accepted"
        assert summary["interest_rate"] == 12.0

    def test_borrower_cannot_access_lender_dashboard(self, borrower_client, mock_db):
        response = borrower_client.get(self.URL)
        assert response.status_code == 403

    def test_unauthenticated_returns_403(self, client, mock_db):
        response = client.get(self.URL)
        assert response.status_code == 403
