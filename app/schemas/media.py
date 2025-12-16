from typing import Optional

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    status: str
    file_name: str
    url: Optional[str] = None
