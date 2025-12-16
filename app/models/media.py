import enum
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db import Base
from app.core.config import settings


class MediaType(enum.Enum):
    id_card = "id_card"
    selfie = "selfie"
    avatar = "avatar"


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    kyc_attempt_id = Column(Integer, ForeignKey("kyc_attempts.id"), nullable=True, index=True)
    type = Column(Enum(MediaType), nullable=False)
    file_path = Column(String, unique=True)
    mime_type = Column(String)
    size_bytes = Column(Integer)
    checksum = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_user = relationship("User", back_populates="media_files")
    kyc_attempt = relationship("KycAttempt", back_populates="media_files")

    @property
    def url(self) -> str:
        if not self.file_path:
            return ""
        base = settings.MEDIA_BASE_URL.rstrip("/")
        return f"{base}/{self.file_path}"
