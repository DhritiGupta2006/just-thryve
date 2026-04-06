from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.consent import Consent
from app.models.loan import Loan
from app.models.user import User
from app.schemas.consent import ConsentGrantRequest, ConsentResponse
from app.services.auth_service import get_current_user
from app.services.aa_service import AAService

router = APIRouter(prefix="/consent", tags=["consent"])

VALID_CONSENT_TYPES = {"bank_statement", "gst_data", "energy_usage", "carbon_audit"}


@router.post("/grant", response_model=List[ConsentResponse], status_code=status.HTTP_201_CREATED)
def grant_consent(
    payload: ConsentGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate loan belongs to user (if borrower)
    loan = db.query(Loan).filter(Loan.id == payload.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    invalid = [ct for ct in payload.consent_types if ct not in VALID_CONSENT_TYPES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid consent types: {invalid}")

    responses = []
    for consent_type in payload.consent_types:
        aa_data = AAService.initiate_consent(
            user_id=str(current_user.id),
            consent_type=consent_type,
            loan_id=payload.loan_id,
        )

        # Auto-simulate grant for mock flow
        artefact = AAService.simulate_grant(consent_type)

        consent = Consent(
            user_id=current_user.id,
            consent_type=consent_type,
            status="granted",
            granted_at=datetime.utcnow(),
            metadata_=artefact,
        )
        db.add(consent)
        db.flush()

        responses.append(
            ConsentResponse(
                consent_id=str(consent.id),
                user_id=str(consent.user_id),
                consent_type=consent.consent_type,
                status=consent.status,
                redirect_url=aa_data["redirect_url"],
                artefact=artefact,
                granted_at=consent.granted_at,
                created_at=consent.created_at,
            )
        )

    db.commit()
    return responses


@router.get("/{consent_id}/status", response_model=ConsentResponse)
def get_consent_status(
    consent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consent = db.query(Consent).filter(Consent.id == consent_id, Consent.user_id == current_user.id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")

    return ConsentResponse(
        consent_id=str(consent.id),
        user_id=str(consent.user_id),
        consent_type=consent.consent_type,
        status=consent.status,
        artefact=consent.metadata_,
        granted_at=consent.granted_at,
        revoked_at=consent.revoked_at,
        created_at=consent.created_at,
    )
