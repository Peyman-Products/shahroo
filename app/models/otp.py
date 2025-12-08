from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db import Base

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    otp_code = Column(String)
    expires_at = Column(DateTime(timezone=True))
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
