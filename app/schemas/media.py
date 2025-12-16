from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.media import MediaType


class Media(BaseModel):
    id: int
    type: MediaType
    url: str
    mime_type: Optional[str]
    size_bytes: Optional[int]
    created_at: datetime
    checksum: Optional[str] = None

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    status: str
    upload_id: int
    url: Optional[str] = None
