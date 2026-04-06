import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    type = Column(
        SAEnum("disbursement", "emi_payment", "penalty", "adjustment", name="transaction_type"),
        nullable=False,
    )
    amount = Column(Numeric(18, 2), nullable=False)
    status = Column(
        SAEnum("initiated", "success", "failed", name="transaction_status"),
        default="initiated",
        nullable=False,
    )
    reference_id = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="transactions")
