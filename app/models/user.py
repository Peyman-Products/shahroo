from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum
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
    address = Column(String, nullable=True)
    id_card_image = Column(String, nullable=True)
    selfie_image = Column(String, nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.unverified)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
