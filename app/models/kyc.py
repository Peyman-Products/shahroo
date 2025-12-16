from sqlalchemy import Column, Integer, String, DateTime, func, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.user import VerificationStatus


class KycAttempt(Base):
    __tablename__ = "kyc_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified)
    reason_codes = Column(String, nullable=True)
    reason_text = Column(String, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    allow_resubmission = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="kyc_attempts", foreign_keys=[user_id])
    media_files = relationship("MediaFile", back_populates="kyc_attempt")
