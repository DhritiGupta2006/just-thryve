"""Route-level tests for /repayment endpoints."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loan(status: str = "disbursed", borrower_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=Decimal("300000.00"),
        approved_amount=Decimal("300000.00"),
        approved_rate=Decimal("12.0000"),
        emi_amount=Decimal("26648.55"),
        tenure_months=12,
        status=status,
        created_at=datetime.utcnow(),
        submitted_at=datetime.utcnow(),
        disbursed_at=datetime.utcnow(),
        closed_at=None,
    )


def _make_schedule_item(loan_id, n: int, status: str = "pending") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        installment_number=n,
        due_date=date(2025, n, 1),
        principal_amount=Decimal("22648.55"),
        interest_amount=Decimal("3000.00"),
        emi_amount=Decimal("25648.55"),
        status=status,
        paid_on=datetime.utcnow() if status == "paid" else None,
    )


# ---------------------------------------------------------------------------
# GET /repayment/schedule
# ---------------------------------------------------------------------------

class TestGetSchedule:
    def test_borrower_can_get_own_schedule(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        items = [_make_schedule_item(loan.id, i) for i in range(1, 4)]

        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = items

        response = borrower_client.get(f"/repayment/schedule?loan_id={loan.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["installment_number"] == 1
        assert "emi_amount" in data[0]
        assert "principal_amount" in data[0]
        assert "interest_amount" in data[0]

    def test_lender_can_get_any_schedule(self, lender_client, mock_db):
        loan = _make_loan()
        items = [_make_schedule_item(loan.id, i) for i in range(1, 3)]

        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = items

        response = lender_client.get(f"/repayment/schedule?loan_id={loan.id}")
        assert response.status_code == 200

    def test_borrower_cannot_get_other_loan_schedule(self, borrower_client, mock_db):
        loan = _make_loan()  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/repayment/schedule?loan_id={loan.id}")
        assert response.status_code == 403

    def test_schedule_for_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(f"/repayment/schedule?loan_id={uuid.uuid4()}")
        assert response.status_code == 404

    def test_schedule_requires_authentication(self, client):
        response = client.get(f"/repayment/schedule?loan_id={uuid.uuid4()}")
        assert response.status_code in (401, 403)

    def test_empty_schedule_returns_empty_list(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        response = borrower_client.get(f"/repayment/schedule?loan_id={loan.id}")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# POST /repayment/pay
# ---------------------------------------------------------------------------

class TestPayRepayment:
    def _payload(self, loan_id):
        return {
            "loan_id": str(loan_id),
            "amount": "25648.55",
            "mandate_id": "NACH-MANDATE-001",
        }

    def test_borrower_can_pay_emi(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="disbursed", borrower_id=borrower.id)
        installment = _make_schedule_item(loan.id, 1, status="pending")

        txn = SimpleNamespace(id=uuid.uuid4(), status="success")

        # Queries: first for loan, then for installment (order_by.first)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = installment
        # pending count after payment = 11 (not last installment)
        mock_db.query.return_value.filter.return_value.count.return_value = 11
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", txn.id) or setattr(obj, "status", "success")

        response = borrower_client.post("/repayment/pay", json=self._payload(loan.id))
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert data["status"] == "success"

    def test_pay_emi_loan_not_in_repayment_phase(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="accepted", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post("/repayment/pay", json=self._payload(loan.id))
        assert response.status_code == 400

    def test_pay_emi_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post("/repayment/pay", json=self._payload(uuid.uuid4()))
        assert response.status_code == 404

    def test_pay_emi_no_pending_installments_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="disbursed", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        response = borrower_client.post("/repayment/pay", json=self._payload(loan.id))
        assert response.status_code == 400

    def test_pay_emi_wrong_borrower_returns_403(self, borrower_client, mock_db):
        loan = _make_loan(status="disbursed")  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post("/repayment/pay", json=self._payload(loan.id))
        assert response.status_code == 403

    def test_pay_emi_requires_authentication(self, client):
        response = client.post("/repayment/pay", json={
            "loan_id": str(uuid.uuid4()),
            "amount": "5000.00",
            "mandate_id": "NACH-001",
        })
        assert response.status_code in (401, 403)

    def test_pay_emi_missing_fields_returns_422(self, borrower_client):
        response = borrower_client.post("/repayment/pay", json={"loan_id": str(uuid.uuid4())})
        assert response.status_code == 422
