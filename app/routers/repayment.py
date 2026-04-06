from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.repayment_schedule import RepaymentSchedule
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.repayment import (
    RepaymentScheduleResponse,
    RepaymentPayRequest,
    RepaymentPayResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/repayment", tags=["repayment"])


@router.get("/schedule", response_model=List[RepaymentScheduleResponse])
def get_schedule(
    loan_id: str = Query(..., description="UUID of the loan"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    schedules = (
        db.query(RepaymentSchedule)
        .filter(RepaymentSchedule.loan_id == loan_id)
        .order_by(RepaymentSchedule.installment_number)
        .all()
    )
    return [
        RepaymentScheduleResponse(
            id=str(s.id),
            loan_id=str(s.loan_id),
            installment_number=s.installment_number,
            due_date=s.due_date,
            principal_amount=s.principal_amount,
            interest_amount=s.interest_amount,
            emi_amount=s.emi_amount,
            status=s.status,
            paid_on=s.paid_on,
        )
        for s in schedules
    ]


@router.post("/pay", response_model=RepaymentPayResponse)
def pay_repayment(
    payload: RepaymentPayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loan = db.query(Loan).filter(Loan.id == payload.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    if loan.status not in ("disbursed", "active"):
        raise HTTPException(status_code=400, detail=f"Loan is not in repayment phase (status: {loan.status})")

    # Find the earliest pending installment
    installment = (
        db.query(RepaymentSchedule)
        .filter(RepaymentSchedule.loan_id == loan.id, RepaymentSchedule.status == "pending")
        .order_by(RepaymentSchedule.installment_number)
        .first()
    )
    if not installment:
        raise HTTPException(status_code=400, detail="No pending installments found")

    txn = Transaction(
        loan_id=loan.id,
        type="emi_payment",
        amount=payload.amount,
        status="success",
        reference_id=payload.mandate_id,
        metadata_={"installment_number": installment.installment_number},
    )
    db.add(txn)

    installment.status = "paid"
    installment.paid_on = datetime.utcnow()
    db.flush()  # flush so the pending count query sees the updated status

    # Check if all installments are paid → close loan
    pending_count = (
        db.query(RepaymentSchedule)
        .filter(RepaymentSchedule.loan_id == loan.id, RepaymentSchedule.status == "pending")
        .count()
    )
    if pending_count == 0:  # this was the last installment
        loan.status = "closed"
        loan.closed_at = datetime.utcnow()
    elif loan.status == "disbursed":
        loan.status = "active"

    db.commit()
    db.refresh(txn)
    return RepaymentPayResponse(transaction_id=str(txn.id), status=txn.status)
