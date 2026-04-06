import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SAEnum("borrower", "lender", name="user_role"), nullable=False)
    kyc_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    business_profiles = relationship("BusinessProfile", back_populates="user", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="borrower", foreign_keys="Loan.borrower_id", cascade="all, delete-orphan")
    offered_loans = relationship("Offer", back_populates="lender", foreign_keys="Offer.lender_id")
    consents = relationship("Consent", back_populates="user", cascade="all, delete-orphan")
