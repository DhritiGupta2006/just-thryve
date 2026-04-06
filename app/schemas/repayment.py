from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel


class RepaymentScheduleResponse(BaseModel):
    id: str
    loan_id: str
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    emi_amount: Decimal
    status: str
    paid_on: Optional[datetime] = None

    class Config:
        from_attributes = True


class RepaymentPayRequest(BaseModel):
    loan_id: str
    amount: Decimal
    mandate_id: str


class RepaymentPayResponse(BaseModel):
    transaction_id: str
    status: str
