import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class MLAuditLog(Base):
    __tablename__ = "ml_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    model_version = Column(String, nullable=False)
    input_features = Column(JSONB, nullable=False)
    prediction_score = Column(Numeric(6, 4), nullable=False)
    shap_values = Column(JSONB, nullable=True)
    decision = Column(String, nullable=False)
    confidence = Column(Numeric(6, 4), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="ml_audit_logs")
