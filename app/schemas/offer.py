from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class OfferCreateRequest(BaseModel):
    loan_id: str
    interest_rate: Decimal
    offered_amount: Decimal
    tenure_months: int


class OfferResponse(BaseModel):
    id: str
    loan_id: str
    lender_id: str
    interest_rate: Decimal
    offered_amount: Decimal
    tenure_months: int
    emi_amount: Decimal
    status: str
    accepted_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
