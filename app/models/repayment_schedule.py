import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_amount = Column(Numeric(18, 2), nullable=False)
    emi_amount = Column(Numeric(18, 2), nullable=False)
    status = Column(
        SAEnum("pending", "paid", "overdue", "waived", name="repayment_status"),
        default="pending",
        nullable=False,
    )
    paid_on = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="repayment_schedules")
