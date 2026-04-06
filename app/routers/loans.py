import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.models.business_profile import BusinessProfile
from app.models.ml_audit_log import MLAuditLog
from app.models.repayment_schedule import RepaymentSchedule
from app.schemas.loan import LoanApplyRequest, LoanResponse
from app.services.auth_service import get_current_user, require_role
from app.services.ml_service import MLService
from app.services.emi_service import EMIService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/loans", tags=["loans"])
settings = get_settings()

_ml_service: Optional[MLService] = None


def get_ml_service() -> MLService:
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService(settings.model_path)
    return _ml_service


def _loan_to_response(loan: Loan) -> LoanResponse:
    return LoanResponse(
        loan_id=str(loan.id),
        borrower_id=str(loan.borrower_id),
        amount_requested=loan.amount_requested,
        purpose=loan.purpose,
        tenure_months=loan.tenure_months,
        status=loan.status,
        approved_amount=loan.approved_amount,
        approved_rate=loan.approved_rate,
        emi_amount=loan.emi_amount,
        risk_score=loan.risk_score,
        ml_decision=loan.ml_decision,
        created_at=loan.created_at,
        submitted_at=loan.submitted_at,
        disbursed_at=loan.disbursed_at,
        closed_at=loan.closed_at,
    )


@router.post("/apply", response_model=dict, status_code=status.HTTP_201_CREATED)
def apply_loan(
    payload: LoanApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    loan = Loan(
        borrower_id=current_user.id,
        amount_requested=payload.amount_requested,
        purpose=payload.purpose,
        tenure_months=payload.tenure_months,
        status="created",
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return {"loan_id": str(loan.id), "status": loan.status}


@router.post("/{loan_id}/submit", response_model=dict)
def submit_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.borrower_id == current_user.id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "created":
        raise HTTPException(status_code=400, detail=f"Cannot submit loan in status '{loan.status}'")

    # Fetch business profile for ML features
    profile: Optional[BusinessProfile] = (
        db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    )

    features = {
        "gst_revenue_3m_avg": float(profile.avg_gst_revenue_3m or 0) if profile else 0.0,
        "gst_revenue_growth_rate": 10.0,
        "gst_revenue_volatility": 0.0,
        "renewable_energy_mix": float(profile.renewable_mix_percent or 0) if profile else 0.0,
        "carbon_emissions_per_revenue": float(profile.carbon_emissions_tons or 0) / max(float(profile.avg_gst_revenue_3m or 1), 1) if profile else 0.0,
        "compliance_status": profile.compliance_status if profile else "pending",
        "loan_amount_requested": float(loan.amount_requested),
        "tenure_months": loan.tenure_months,
        "sector": profile.sector if profile else "commerce",
    }

    result = ml_service.predict(features)

    loan.status = "submitted"
    loan.submitted_at = datetime.utcnow()
    loan.risk_score = result["risk_score"]
    loan.ml_decision = result["decision"]

    audit = MLAuditLog(
        loan_id=loan.id,
        model_version=result["model_version"],
        input_features=result["input_features"],
        prediction_score=result["confidence"],
        shap_values=result.get("shap_values"),
        decision=result["decision"],
        confidence=result["confidence"],
    )
    db.add(audit)
    db.commit()

    return {"loan_id": str(loan.id), "status": loan.status, "ml_decision": result["decision"], "risk_score": result["risk_score"]}


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    # Borrowers can only see their own loans; lenders can see all
    if current_user.role == "borrower" and str(loan.borrower_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return _loan_to_response(loan)


@router.post("/{loan_id}/accept-offer/{offer_id}", response_model=dict)
def accept_offer(
    loan_id: str,
    offer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("borrower")),
):
    from app.models.offer import Offer

    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.borrower_id == current_user.id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "offers_received":
        raise HTTPException(status_code=400, detail="No offers available to accept")

    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.loan_id == loan_id, Offer.status == "pending").first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or already processed")

    # Reject all other offers
    db.query(Offer).filter(Offer.loan_id == loan_id, Offer.id != offer_id).update({"status": "rejected"})

    offer.status = "accepted"
    offer.accepted_at = datetime.utcnow()
    loan.status = "accepted"
    loan.approved_amount = offer.offered_amount
    loan.approved_rate = offer.interest_rate
    loan.emi_amount = offer.emi_amount

    db.commit()
    return {
        "loan_id": str(loan.id),
        "status": loan.status,
        "disbursement_scheduled": True,
        "offer_id": str(offer.id),
    }


@router.post("/{loan_id}/disburse", response_model=dict)
def disburse_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as _uuid
    from app.models.transaction import Transaction

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "accepted":
        raise HTTPException(status_code=400, detail=f"Cannot disburse loan in status '{loan.status}'")

    ref_id = f"DISB-{str(_uuid.uuid4())[:8].upper()}"
    txn = Transaction(
        loan_id=loan.id,
        type="disbursement",
        amount=loan.approved_amount,
        status="initiated",
        reference_id=ref_id,
        metadata_={"note": "Mock UPI disbursement initiated"},
    )
    db.add(txn)

    # Simulate successful disbursement and generate repayment schedule
    txn.status = "success"
    loan.status = "disbursed"
    loan.disbursed_at = datetime.utcnow()

    _generate_repayment_schedule(loan, db)

    db.commit()
    db.refresh(txn)
    return {"disbursement_id": str(txn.id), "status": "initiated", "reference_id": ref_id}


def _generate_repayment_schedule(loan: Loan, db: Session):
    from datetime import date
    from dateutil.relativedelta import relativedelta  # type: ignore

    # approved_rate is stored in percentage form (e.g. 12.0 for 12% p.a.)
    rate = float(loan.approved_rate or 0)
    principal = float(loan.approved_amount or loan.amount_requested)
    schedule_items = EMIService.generate_amortization_schedule(principal, rate, loan.tenure_months)

    today = loan.disbursed_at.date() if loan.disbursed_at else datetime.utcnow().date()
    for item in schedule_items:
        due = today + relativedelta(months=item["installment_number"])
        rs = RepaymentSchedule(
            loan_id=loan.id,
            installment_number=item["installment_number"],
            due_date=due,
            principal_amount=item["principal_amount"],
            interest_amount=item["interest_amount"],
            emi_amount=item["emi_amount"],
            status="pending",
        )
        db.add(rs)
