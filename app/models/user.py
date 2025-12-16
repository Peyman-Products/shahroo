from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
import enum

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
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified)
    avatar_media_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    active_id_card_media_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    active_selfie_media_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    current_kyc_attempt_id = Column(Integer, ForeignKey("kyc_attempts.id"), nullable=True)
    kyc_locked_at = Column(DateTime(timezone=True), nullable=True)
    kyc_last_reason_codes = Column(String, nullable=True)
    kyc_last_reason_text = Column(String, nullable=True)
    kyc_last_decided_at = Column(DateTime(timezone=True), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")
    media_files = relationship(
        "MediaFile",
        back_populates="owner_user",
        foreign_keys="MediaFile.owner_user_id",
    )
    avatar_media = relationship("MediaFile", foreign_keys=[avatar_media_id])
    id_card_media = relationship("MediaFile", foreign_keys=[active_id_card_media_id])
    selfie_media = relationship("MediaFile", foreign_keys=[active_selfie_media_id])
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
        return self.avatar_media.url if self.avatar_media else None
