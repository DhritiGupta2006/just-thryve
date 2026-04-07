"""
AuditLogService — encapsulates business-logic queries for ML audit log access,
extracted from the audit_logs router.
"""
from typing import Any, List, Optional


class AuditLogService:
    @staticmethod
    def to_response_dict(log: Any) -> dict:
        """Convert an MLAuditLog ORM object to a serialisable dict."""
        return {
            "id": str(log.id),
            "loan_id": str(log.loan_id),
            "model_version": log.model_version,
            "input_features": log.input_features,
            "prediction_score": log.prediction_score,
            "shap_values": log.shap_values,
            "decision": log.decision,
            "confidence": log.confidence,
            "created_at": log.created_at,
        }
