from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class LoanApplyRequest(BaseModel):
    amount_requested: Decimal
    purpose: str
    tenure_months: int


class LoanResponse(BaseModel):
    loan_id: str
    borrower_id: str
    amount_requested: Decimal
    purpose: str
    tenure_months: int
    status: str
    approved_amount: Optional[Decimal] = None
    approved_rate: Optional[Decimal] = None
    emi_amount: Optional[Decimal] = None
    risk_score: Optional[int] = None
    ml_decision: Optional[str] = None
    created_at: datetime
    submitted_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
