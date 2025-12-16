import hashlib
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.media import MediaFile, MediaType


class MediaManager:
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

    def __init__(self, base_dir: str | Path | None = None):
        self.base_path = Path(base_dir or settings.MEDIA_ROOT)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = self.MAX_FILE_SIZE_BYTES

    def _validate_upload(self, upload_file: UploadFile):
        if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    def _validate_file_size(self, size_bytes: int):
        if size_bytes > self.max_file_size_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file exceeds 20MB limit")

    def _folder_for(self, user_id: int, media_type: MediaType) -> Path:
        if media_type == MediaType.avatar:
            return self.base_path / "users" / str(user_id) / "avatar"
        if media_type == MediaType.id_card:
            return self.base_path / "users" / str(user_id) / "kyc" / "id-card"
        if media_type == MediaType.selfie:
            return self.base_path / "users" / str(user_id) / "kyc" / "selfie"
        raise HTTPException(status_code=400, detail="Unsupported media type")

    def save_user_media(
        self,
        db: Session,
        *,
        user_id: int,
        media_type: MediaType,
        upload_file: UploadFile,
        kyc_attempt_id: int | None = None,
    ) -> MediaFile:
        self._validate_upload(upload_file)

        target_folder = self._folder_for(user_id, media_type)
        target_folder.mkdir(parents=True, exist_ok=True)

        file_suffix = Path(upload_file.filename).suffix or ""
        filename = f"{uuid.uuid4()}{file_suffix}"
        relative_path = (target_folder / filename).relative_to(self.base_path)
        absolute_path = self.base_path / relative_path

        content = upload_file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        checksum = hashlib.sha256(content).hexdigest()
        size_bytes = len(content)
        self._validate_file_size(size_bytes)

        with open(absolute_path, "wb") as buffer:
            buffer.write(content)

        upload_file.file.seek(0)

        db.query(MediaFile).filter(
            MediaFile.owner_user_id == user_id,
            MediaFile.type == media_type,
            MediaFile.is_active == True,
        ).update({"is_active": False})

        media = MediaFile(
            owner_user_id=user_id,
            type=media_type,
            file_path=str(relative_path).replace("\\", "/"),
            mime_type=upload_file.content_type,
            size_bytes=size_bytes,
            checksum=checksum,
            kyc_attempt_id=kyc_attempt_id,
            is_active=True,
        )
        db.add(media)
        db.flush()
        return media
