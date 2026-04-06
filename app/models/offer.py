import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    lender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    interest_rate = Column(Numeric(6, 4), nullable=False)
    offered_amount = Column(Numeric(18, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(18, 2), nullable=False)
    status = Column(
        SAEnum("pending", "accepted", "rejected", "expired", name="offer_status"),
        default="pending",
        nullable=False,
    )
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="offers")
    lender = relationship("User", back_populates="offered_loans", foreign_keys=[lender_id])
