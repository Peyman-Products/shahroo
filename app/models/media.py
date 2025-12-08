from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, unique=True)
    mime_type = Column(String)
    size_bytes = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_user = relationship("User")
