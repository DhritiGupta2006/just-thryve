from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.ml_audit_log import MLAuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _to_response(log: MLAuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=str(log.id),
        loan_id=str(log.loan_id),
        model_version=log.model_version,
        input_features=log.input_features,
        prediction_score=log.prediction_score,
        shap_values=log.shap_values,
        decision=log.decision,
        confidence=log.confidence,
        created_at=log.created_at,
    )


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    loan_id: Optional[str] = Query(None, description="Filter by loan UUID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MLAuditLog)

    if loan_id:
        # Verify the loan exists and the user has access
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        query = query.filter(MLAuditLog.loan_id == loan_id)
    elif current_user.role == "borrower":
        # Borrowers only see audit logs for their own loans
        borrower_loan_ids = [
            row.id for row in db.query(Loan.id).filter(Loan.borrower_id == current_user.id).all()
        ]
        query = query.filter(MLAuditLog.loan_id.in_(borrower_loan_ids))

    logs = query.order_by(MLAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_response(log) for log in logs]


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(MLAuditLog).filter(MLAuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    # Borrowers can only access audit logs for their own loans
    if current_user.role == "borrower":
        loan = db.query(Loan).filter(Loan.id == log.loan_id).first()
        if not loan or str(loan.borrower_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    return _to_response(log)
