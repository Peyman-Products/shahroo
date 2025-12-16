from pathlib import Path
import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.db import Base

class VerificationStatus(enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    birthdate = Column(Date, nullable=True)
    sex = Column(String, nullable=True)
    national_id = Column(String, unique=True, nullable=True)
    shaba_number = Column(String, unique=True, nullable=True)
    address = Column(String, nullable=True)
    id_card_image = Column(String, nullable=True)
    selfie_image = Column(String, nullable=True)
    avatar_image = Column(String, nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified)
    current_kyc_attempt_id = Column(Integer, ForeignKey("kyc_attempts.id"), nullable=True)
    kyc_locked_at = Column(DateTime(timezone=True), nullable=True)
    kyc_last_reason_codes = Column(String, nullable=True)
    kyc_last_reason_text = Column(String, nullable=True)
    kyc_last_decided_at = Column(DateTime(timezone=True), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")
    kyc_attempts = relationship(
        "KycAttempt",
        back_populates="user",
        foreign_keys="KycAttempt.user_id",
    )
    current_kyc_attempt = relationship("KycAttempt", foreign_keys=[current_kyc_attempt_id])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def avatar_url(self):
        if not self.avatar_image:
            return None
        base = settings.MEDIA_BASE_URL.rstrip("/")
        normalized_path = str(Path(self.avatar_image)).lstrip("/")
        return f"{base}/{normalized_path}"
