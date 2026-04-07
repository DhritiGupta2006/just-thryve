import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    sector = Column(String, nullable=False)  # renewable_energy, agriculture, commerce
    registration_number = Column(String, nullable=True)
    gst_number = Column(String, unique=True, nullable=True)
    avg_gst_revenue_3m = Column(Numeric(18, 2), nullable=True)
    renewable_mix_percent = Column(Integer, default=0, nullable=False)
    carbon_emissions_tons = Column(Numeric(10, 4), nullable=True)
    compliance_status = Column(String, default="pending", nullable=False)  # compliant, pending, non_compliant
    waste_recycled_percent = Column(Numeric(5, 2), default=0, nullable=False)
    social_impact_score = Column(Numeric(5, 2), default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="business_profiles")
