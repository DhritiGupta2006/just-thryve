"""Tests for new loan intelligence endpoints:
  GET /loans/{id}/risk-explanation
  GET /loans/{id}/comparisons
  POST /loans/{id}/early-repayment
  GET /loans/{id}/transactions
"""
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest


def _make_loan(status="disbursed", borrower_id=None, **kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        borrower_id=borrower_id or uuid.uuid4(),
        amount_requested=Decimal("500000.00"),
        purpose="Solar installation",
        tenure_months=12,
        status=status,
        approved_amount=kwargs.get("approved_amount", Decimal("500000.00")),
        approved_rate=kwargs.get("approved_rate", Decimal("12.0000")),
        emi_amount=kwargs.get("emi_amount", Decimal("44424.40")),
        risk_score=kwargs.get("risk_score", 750),
        ml_decision=kwargs.get("ml_decision", "approved"),
        created_at=datetime.utcnow(),
        submitted_at=datetime.utcnow(),
        disbursed_at=datetime.utcnow(),
        closed_at=None,
    )


def _make_audit_log(loan_id) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        model_version="heuristic-1.0",
        input_features={"gst_revenue_3m_avg": 500000.0},
        prediction_score=Decimal("0.8500"),
        shap_values={"gst_revenue_3m_avg": 0.25, "renewable_energy_mix": 0.20},
        decision="approved",
        confidence=Decimal("0.8500"),
        created_at=datetime.utcnow(),
    )


def _make_offer(loan_id, lender_id=None, status="pending") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        lender_id=lender_id or uuid.uuid4(),
        interest_rate=Decimal("12.0000"),
        offered_amount=Decimal("500000.00"),
        tenure_months=12,
        emi_amount=Decimal("44424.40"),
        status=status,
        accepted_at=None,
        expires_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


def _make_schedule_item(loan_id, n=1, status="pending") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        installment_number=n,
        due_date=__import__("datetime").date(2026, n % 12 + 1, 1),
        principal_amount=Decimal("40000.00"),
        interest_amount=Decimal("4424.40"),
        emi_amount=Decimal("44424.40"),
        status=status,
        paid_on=None,
    )


def _make_transaction(loan_id, txn_type="disbursement") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        loan_id=loan_id,
        type=txn_type,
        amount=Decimal("500000.00"),
        status="success",
        reference_id="DISB-ABCD1234",
        metadata_={"note": "test"},
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# GET /loans/{id}/risk-explanation
# ---------------------------------------------------------------------------

class TestRiskExplanation:
    def test_borrower_gets_explanation_for_own_loan(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        audit = _make_audit_log(loan.id)

        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = audit

        response = borrower_client.get(f"/loans/{loan.id}/risk-explanation")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "risk_level" in data
        assert "decision" in data
        assert "factors" in data
        assert "recommendations" in data

    def test_explanation_without_audit_log(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id, ml_decision="approved", risk_score=750)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        response = borrower_client.get(f"/loans/{loan.id}/risk-explanation")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "approved"
        assert data["risk_score"] == 750

    def test_borrower_cannot_get_other_loan_explanation(self, borrower_client, mock_db):
        loan = _make_loan()  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/loans/{loan.id}/risk-explanation")
        assert response.status_code == 403

    def test_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(f"/loans/{uuid.uuid4()}/risk-explanation")
        assert response.status_code == 404

    def test_lender_can_get_any_loan_explanation(self, lender_client, mock_db):
        loan = _make_loan()
        audit = _make_audit_log(loan.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = audit

        response = lender_client.get(f"/loans/{loan.id}/risk-explanation")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /loans/{id}/comparisons
# ---------------------------------------------------------------------------

class TestLoanComparisons:
    def test_returns_comparisons_with_recommendation(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        o1 = _make_offer(loan.id)
        o2 = _make_offer(loan.id)
        o2.interest_rate = Decimal("10.0000")
        o2.emi_amount = Decimal("43800.00")

        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.all.return_value = [o1, o2]

        response = borrower_client.get(f"/loans/{loan.id}/comparisons")
        assert response.status_code == 200
        data = response.json()
        assert "comparisons" in data
        assert "recommended_offer_id" in data
        assert "summary" in data
        assert len(data["comparisons"]) == 2

    def test_comparison_includes_total_cost(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        offer = _make_offer(loan.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.all.return_value = [offer]

        response = borrower_client.get(f"/loans/{loan.id}/comparisons")
        assert response.status_code == 200
        comparison = response.json()["comparisons"][0]
        assert "total_payment" in comparison
        assert "total_interest_paid" in comparison

    def test_no_offers_returns_empty_comparisons(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = borrower_client.get(f"/loans/{loan.id}/comparisons")
        assert response.status_code == 200
        assert response.json()["comparisons"] == []

    def test_borrower_cannot_compare_other_loan(self, borrower_client, mock_db):
        loan = _make_loan()  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/loans/{loan.id}/comparisons")
        assert response.status_code == 403

    def test_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(f"/loans/{uuid.uuid4()}/comparisons")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /loans/{id}/early-repayment
# ---------------------------------------------------------------------------

class TestEarlyRepayment:
    def _payload(self, prepayment_amount=100000.0, penalty_percent=2.0):
        return {
            "prepayment_amount": prepayment_amount,
            "prepayment_penalty_percent": penalty_percent,
        }

    def test_borrower_gets_early_repayment_estimate(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="active", borrower_id=borrower.id)
        pending = [_make_schedule_item(loan.id, i) for i in range(1, 7)]

        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = pending

        response = borrower_client.post(
            f"/loans/{loan.id}/early-repayment",
            json=self._payload(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "outstanding_principal" in data
        assert "prepayment_amount" in data
        assert "estimated_savings" in data
        assert "prepayment_penalty" in data
        assert "fully_repaid" in data

    def test_loan_not_in_active_status_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="submitted", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.post(
            f"/loans/{loan.id}/early-repayment",
            json=self._payload(),
        )
        assert response.status_code == 400

    def test_no_pending_installments_returns_400(self, borrower_client, mock_db, borrower):
        loan = _make_loan(status="disbursed", borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        response = borrower_client.post(
            f"/loans/{loan.id}/early-repayment",
            json=self._payload(),
        )
        assert response.status_code == 400

    def test_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.post(
            f"/loans/{uuid.uuid4()}/early-repayment",
            json=self._payload(),
        )
        assert response.status_code == 404

    def test_lender_cannot_request_early_repayment(self, lender_client, mock_db):
        response = lender_client.post(
            f"/loans/{uuid.uuid4()}/early-repayment",
            json=self._payload(),
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /loans/{id}/transactions
# ---------------------------------------------------------------------------

class TestLoanTransactions:
    def test_borrower_gets_own_loan_transactions(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        txns = [
            _make_transaction(loan.id, "disbursement"),
            _make_transaction(loan.id, "emi_payment"),
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = txns

        response = borrower_client.get(f"/loans/{loan.id}/transactions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["type"] == "disbursement"
        assert "amount" in data[0]
        assert "status" in data[0]
        assert "reference_id" in data[0]

    def test_empty_transactions_returns_empty_list(self, borrower_client, mock_db, borrower):
        loan = _make_loan(borrower_id=borrower.id)
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        response = borrower_client.get(f"/loans/{loan.id}/transactions")
        assert response.status_code == 200
        assert response.json() == []

    def test_borrower_cannot_get_other_loan_transactions(self, borrower_client, mock_db):
        loan = _make_loan()  # different borrower_id
        mock_db.query.return_value.filter.return_value.first.return_value = loan

        response = borrower_client.get(f"/loans/{loan.id}/transactions")
        assert response.status_code == 403

    def test_lender_can_get_any_loan_transactions(self, lender_client, mock_db):
        loan = _make_loan()
        txns = [_make_transaction(loan.id)]
        mock_db.query.return_value.filter.return_value.first.return_value = loan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = txns

        response = lender_client.get(f"/loans/{loan.id}/transactions")
        assert response.status_code == 200

    def test_nonexistent_loan_returns_404(self, borrower_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = borrower_client.get(f"/loans/{uuid.uuid4()}/transactions")
        assert response.status_code == 404

    def test_unauthenticated_returns_403(self, client):
        response = client.get(f"/loans/{uuid.uuid4()}/transactions")
        assert response.status_code in (401, 403)
