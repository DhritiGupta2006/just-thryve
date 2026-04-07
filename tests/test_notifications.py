"""Tests for GET /notifications endpoint."""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest


def _make_loan(borrower_id=None, status: str = "disbursed", amount_requested=Decimal("500000.00")) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=amount_requested,
        status=status,
        created_at=datetime(2026, 1, 1),
        submitted_at=datetime(2026, 1, 2),
        disbursed_at=datetime(2026, 1, 3),
        closed_at=None,
    )


def _make_repayment(
    loan_id=None,
    status: str = "pending",
    emi_amount=Decimal("44424.40"),
    due_date: date = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id or uuid.uuid4(),
        installment_number=1,
        due_date=due_date or date.today() + timedelta(days=3),
        principal_amount=Decimal("40000.00"),
        interest_amount=Decimal("4424.40"),
        emi_amount=emi_amount,
        status=status,
        paid_on=None,
    )


def _make_offer(
    lender_id=None,
    loan_id=None,
    status: str = "accepted",
    offered_amount=Decimal("500000.00"),
    interest_rate=Decimal("12.0000"),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id or uuid.uuid4(),
        lender_id=lender_id or uuid.uuid4(),
        offered_amount=offered_amount,
        interest_rate=interest_rate,
        tenure_months=12,
        emi_amount=Decimal("44424.40"),
        status=status,
        accepted_at=datetime(2026, 1, 5),
        expires_at=datetime(2026, 2, 5),
        created_at=datetime(2026, 1, 4),
    )


class _QueryBuilder:
    """Minimal mock that returns preset values for .all() and .first() calls.

    ``all_results`` is a list-of-lists: the nth call to ``.all()`` returns
    ``all_results[n]``, falling back to ``[]`` once the list is exhausted.
    Pass a plain list to get the same result on every call.
    """

    def __init__(self, all_results=None, first_result=None):
        # Normalise: if a plain list of objects (not list-of-lists) was passed,
        # treat it as [results] so the first .all() call returns it and
        # subsequent calls return [].
        raw = all_results or []
        if raw and not isinstance(raw[0], list):
            self._all_results = [raw]
        else:
            self._all_results = raw
        self._call_count = 0
        self._first = first_result

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, *args):
        return self

    def all(self):
        idx = self._call_count
        self._call_count += 1
        if idx < len(self._all_results):
            return self._all_results[idx]
        return []

    def first(self):
        return self._first


class TestBorrowerNotifications:
    URL = "/notifications"

    def test_returns_empty_list_when_no_activity(self, borrower_client, mock_db):
        mock_db.query.return_value = _QueryBuilder()
        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        assert response.json() == []

    def test_disbursed_loan_generates_status_notification(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id, status="disbursed")
        mock_db.query.return_value = _QueryBuilder(all_results=[loan])

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        # Should include a status notification for disbursed
        titles = [n["title"] for n in data]
        assert any("Disbursed" in t or "Status" in t or "Loan" in t for t in titles)

    def test_submitted_loan_generates_notification(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id, status="submitted")
        mock_db.query.return_value = _QueryBuilder(all_results=[loan])

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        titles = [n["title"] for n in data]
        assert any("Submitted" in t for t in titles)

    def test_upcoming_emi_generates_notification(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        upcoming = _make_repayment(loan_id=loan.id, status="pending")

        call_count = [0]

        class _MultiQueryBuilder:
            def filter(self_inner, *args):
                return self_inner

            def order_by(self_inner, *args):
                return self_inner

            def limit(self_inner, *args):
                return self_inner

            def all(self_inner):
                call_count[0] += 1
                if call_count[0] == 1:
                    return [loan]
                if call_count[0] == 2:
                    return [upcoming]  # upcoming EMIs
                return []  # overdue EMIs

            def first(self_inner):
                return None

        mock_db.query.return_value = _MultiQueryBuilder()

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        titles = [n["title"] for n in data]
        assert any("EMI" in t or "Payment" in t for t in titles)

    def test_notification_has_required_fields(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id, status="submitted")
        mock_db.query.return_value = _QueryBuilder(all_results=[loan])

        response = borrower_client.get(self.URL)
        assert response.status_code == 200
        if response.json():
            note = response.json()[0]
            assert "id" in note
            assert "title" in note
            assert "description" in note
            assert "category" in note
            assert "created_at" in note

    def test_unauthenticated_returns_403(self, client, mock_db):
        response = client.get(self.URL)
        assert response.status_code == 403


class TestLenderNotifications:
    URL = "/notifications"

    def test_accepted_offer_generates_notification(self, lender_client, mock_db, lender):
        offer = _make_offer(lender_id=lender.id, status="accepted")
        mock_db.query.return_value = _QueryBuilder(all_results=[offer])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        titles = [n["title"] for n in data]
        assert any("Accepted" in t for t in titles)

    def test_rejected_offer_generates_notification(self, lender_client, mock_db, lender):
        offer = _make_offer(lender_id=lender.id, status="rejected")
        mock_db.query.return_value = _QueryBuilder(all_results=[offer])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        data = response.json()
        titles = [n["title"] for n in data]
        assert any("Not Selected" in t or "Rejected" in t for t in titles)

    def test_pending_offer_generates_no_notification(self, lender_client, mock_db, lender):
        offer = _make_offer(lender_id=lender.id, status="pending")
        mock_db.query.return_value = _QueryBuilder(all_results=[offer])

        response = lender_client.get(self.URL)
        assert response.status_code == 200
        # Pending offers don't generate notifications
        assert response.json() == []
