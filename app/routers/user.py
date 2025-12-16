from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import get_db
from app.schemas.user import User as UserSchema, UserUpdate
from app.schemas.kyc import KycStatusResponse, KycDecision
from app.schemas.media import MediaUploadResponse
from app.models.user import User, VerificationStatus
from app.models.media import MediaType
from app.models.kyc import KycAttempt
from app.utils.deps import get_current_user
from app.utils.media import MediaManager

router = APIRouter()
media_manager = MediaManager()


def _reset_rejection_state(user: User, attempt: KycAttempt | None):
    user.kyc_last_reason_codes = None
    user.kyc_last_reason_text = None
    user.kyc_last_decided_at = None
    if attempt:
        attempt.reason_codes = None
        attempt.reason_text = None
        attempt.decided_at = None


def _get_or_create_attempt(db: Session, user: User) -> KycAttempt:
    if user.current_kyc_attempt and user.verification_status != VerificationStatus.rejected:
        return user.current_kyc_attempt
    attempt = KycAttempt(user_id=user.id, status=VerificationStatus.unverified, allow_resubmission=True)
    db.add(attempt)
    db.flush()
    user.current_kyc_attempt_id = attempt.id
    user.verification_status = VerificationStatus.unverified
    _reset_rejection_state(user, attempt)
    return attempt


def _ensure_can_upload_kyc(user: User):
    if user.verification_status == VerificationStatus.verified:
        raise HTTPException(status_code=403, detail="KYC is already verified and locked")
    if user.verification_status == VerificationStatus.pending:
        raise HTTPException(status_code=403, detail="KYC is pending review and cannot be changed")


def _maybe_mark_pending(user: User, attempt: KycAttempt):
    if user.active_id_card_media_id and user.active_selfie_media_id:
        attempt.status = VerificationStatus.pending
        attempt.submitted_at = datetime.now(timezone.utc)
        user.verification_status = VerificationStatus.pending


def _last_decision(user: User) -> KycDecision | None:
    codes = user.kyc_last_reason_codes.split(",") if user.kyc_last_reason_codes else None
    if user.kyc_last_decided_at:
        return KycDecision(
            status=user.verification_status,
            reason_codes=codes,
            reason_text=user.kyc_last_reason_text,
            decided_at=user.kyc_last_decided_at,
        )

    attempt = user.current_kyc_attempt
    if attempt and attempt.decided_at:
        codes = attempt.reason_codes.split(",") if attempt.reason_codes else None
        return KycDecision(
            status=attempt.status,
            reason_codes=codes,
            reason_text=attempt.reason_text,
            decided_at=attempt.decided_at,
        )
    return None


@router.get("/me", response_model=UserSchema, summary="Get current user profile")
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the profile of the currently authenticated user.
    """
    current_user.last_decision = _last_decision(current_user)
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
    current_user.last_decision = _last_decision(current_user)
    return current_user


@router.post("/me/kyc/id-card", response_model=MediaUploadResponse, summary="Upload ID card image")
def upload_id_card(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Uploads an ID card image for the current user.
    """
    _ensure_can_upload_kyc(current_user)
    attempt = _get_or_create_attempt(db, current_user)

    media = media_manager.save_user_media(
        db,
        user_id=current_user.id,
        media_type=MediaType.id_card,
        upload_file=file,
        kyc_attempt_id=attempt.id,
    )
    current_user.active_id_card_media_id = media.id
    current_user.id_card_image = None
    _maybe_mark_pending(current_user, attempt)
    db.commit()
    db.refresh(media)
    return MediaUploadResponse(status="uploaded", upload_id=media.id)


@router.post("/me/kyc/selfie", response_model=MediaUploadResponse, summary="Upload selfie image")
def upload_selfie(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Uploads a selfie image for the current user.
    """
    _ensure_can_upload_kyc(current_user)
    attempt = _get_or_create_attempt(db, current_user)

    media = media_manager.save_user_media(
        db,
        user_id=current_user.id,
        media_type=MediaType.selfie,
        upload_file=file,
        kyc_attempt_id=attempt.id,
    )
    current_user.active_selfie_media_id = media.id
    current_user.selfie_image = None
    _maybe_mark_pending(current_user, attempt)
    db.commit()
    db.refresh(media)
    return MediaUploadResponse(status="uploaded", upload_id=media.id)


@router.post("/me/avatar", response_model=MediaUploadResponse, summary="Upload avatar image")
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    media = media_manager.save_user_media(
        db,
        user_id=current_user.id,
        media_type=MediaType.avatar,
        upload_file=file,
    )
    current_user.avatar_media_id = media.id
    db.commit()
    db.refresh(media)
    return MediaUploadResponse(status="uploaded", upload_id=media.id, url=media.url)


@router.get("/me/kyc/status", response_model=KycStatusResponse, summary="Get KYC status summary")
def kyc_status(current_user: User = Depends(get_current_user)):
    last_decision = _last_decision(current_user)
    return KycStatusResponse(
        verification_status=current_user.verification_status,
        last_decision=last_decision,
        can_upload_kyc=current_user.verification_status in {VerificationStatus.unverified, VerificationStatus.rejected},
    )
