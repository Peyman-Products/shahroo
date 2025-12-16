from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import get_db
from app.schemas.user import User as UserSchema, UserUpdate
from app.models.user import User, VerificationStatus
from app.utils.deps import get_current_user
import shutil
import os
import uuid
from app.models.media import MediaFile

router = APIRouter()

@router.get("/me", response_model=UserSchema, summary="Get current user profile")
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the profile of the currently authenticated user.
    """
    return current_user

@router.patch("/me", response_model=UserSchema, summary="Update current user profile")
def update_user_me(user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Updates the profile of the currently authenticated user.
    """
    updates = user_in.dict(exclude_unset=True)

    unique_fields = {
        "national_id": "National ID",
        "shaba_number": "Shaba number",
    }

    for field, label in unique_fields.items():
        value = updates.get(field)
        if value:
            existing_user = db.query(User).filter(getattr(User, field) == value, User.id != current_user.id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail=f"{label} already in use by another user")

    for field, value in updates.items():
        setattr(current_user, field, value)
    db.add(current_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unique constraint violated while updating profile")
    db.refresh(current_user)
    return current_user

@router.post("/me/id-card", summary="Upload ID card image")
def upload_id_card(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Uploads an ID card image for the current user.
    """
    media_dir = f"media/{current_user.id}"
    os.makedirs(media_dir, exist_ok=True)
    file_extension = file.filename.split(".")[-1]
    file_path = f"{media_dir}/{uuid.uuid4()}.{file_extension}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_media_file = MediaFile(
        owner_user_id=current_user.id,
        file_path=file_path,
        mime_type=file.content_type,
        size_bytes=file.file.tell()
    )
    db.add(db_media_file)

    current_user.id_card_image = file_path
    if current_user.selfie_image:
        current_user.verification_status = VerificationStatus.pending
    db.commit()

    return {"filename": file.filename, "path": file_path}

@router.post("/me/selfie", summary="Upload selfie image")
def upload_selfie(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Uploads a selfie image for the current user.
    """
    media_dir = f"media/{current_user.id}"
    os.makedirs(media_dir, exist_ok=True)
    file_extension = file.filename.split(".")[-1]
    file_path = f"{media_dir}/{uuid.uuid4()}.{file_extension}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_media_file = MediaFile(
        owner_user_id=current_user.id,
        file_path=file_path,
        mime_type=file.content_type,
        size_bytes=file.file.tell()
    )
    db.add(db_media_file)

    current_user.selfie_image = file_path
    if current_user.id_card_image:
        current_user.verification_status = VerificationStatus.pending
    db.commit()

    return {"filename": file.filename, "path": file_path}
