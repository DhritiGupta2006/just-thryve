from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: str
    loan_id: str
    type: str
    amount: Decimal
    status: str
    reference_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
