from pydantic import BaseModel
from datetime import datetime

class MediaFileBase(BaseModel):
    file_path: str
    mime_type: str
    size_bytes: int

class MediaFileCreate(MediaFileBase):
    pass

class MediaFile(MediaFileBase):
    id: int
    owner_user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
