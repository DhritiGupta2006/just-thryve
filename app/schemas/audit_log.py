from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    loan_id: str
    model_version: str
    input_features: Dict[str, Any]
    prediction_score: Decimal
    shap_values: Optional[Dict[str, Any]] = None
    decision: str
    confidence: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True
