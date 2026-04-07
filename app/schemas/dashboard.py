from typing import List, Optional

from pydantic import BaseModel


class LoanSummary(BaseModel):
    loan_id: str
    status: str
    amount_requested: float
    approved_amount: Optional[float] = None
    emi_amount: Optional[float] = None
    risk_score: Optional[int] = None
    ml_decision: Optional[str] = None
    created_at: str


class OfferSummary(BaseModel):
    offer_id: str
    loan_id: str
    status: str
    offered_amount: float
    interest_rate: float
    tenure_months: int
    emi_amount: float
    created_at: str


class BorrowerDashboardResponse(BaseModel):
    loan_count: int
    active_loan_count: int
    total_requested: float
    total_approved: float
    total_repaid: float
    next_emi_date: Optional[str] = None
    next_emi_amount: Optional[float] = None
    loans: List[LoanSummary]


class LenderDashboardResponse(BaseModel):
    offer_count: int
    accepted_offer_count: int
    portfolio_value: float
    average_interest_rate: Optional[float] = None
    offers: List[OfferSummary]
