import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    borrower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount_requested = Column(Numeric(18, 2), nullable=False)
    purpose = Column(String, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    status = Column(
        SAEnum(
            "created", "submitted", "offers_received", "accepted",
            "disbursed", "active", "closed",
            name="loan_status",
        ),
        default="created",
        nullable=False,
    )
    approved_amount = Column(Numeric(18, 2), nullable=True)
    approved_rate = Column(Numeric(6, 4), nullable=True)
    emi_amount = Column(Numeric(18, 2), nullable=True)
    risk_score = Column(Integer, nullable=True)
    ml_decision = Column(String, nullable=True)  # approved, rejected, manual_review
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    disbursed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    borrower = relationship("User", back_populates="loans", foreign_keys=[borrower_id])
    offers = relationship("Offer", back_populates="loan", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="loan", cascade="all, delete-orphan")
    repayment_schedules = relationship("RepaymentSchedule", back_populates="loan", cascade="all, delete-orphan")
    ml_audit_logs = relationship("MLAuditLog", back_populates="loan", cascade="all, delete-orphan")
