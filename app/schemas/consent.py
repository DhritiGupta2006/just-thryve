from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class ConsentGrantRequest(BaseModel):
    loan_id: str
    consent_types: List[str]  # bank_statement, gst_data, energy_usage, carbon_audit


class ConsentResponse(BaseModel):
    consent_id: str
    user_id: str
    consent_type: str
    status: str
    redirect_url: Optional[str] = None
    artefact: Optional[Any] = None
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
