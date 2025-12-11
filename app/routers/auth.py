from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.otp import OTPSend, OTPVerify, OTPAdminLookup, OTPAdminLookupResponse
from app.schemas.user import User as UserSchema
from app.models.user import User, VerificationStatus
from app.utils.otp import (
    send_otp as send_otp_util,
    verify_otp as verify_otp_util,
    get_valid_otp,
)
from app.utils.token import create_access_token
from app.utils.deps import get_current_user

router = APIRouter()


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.role or current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/send-otp", summary="Send OTP to user")
def send_otp(otp_send: OTPSend, db: Session = Depends(get_db)):
    """
    Sends an OTP to the user's phone number.
    """
    send_otp_util(db, otp_send.phone_number)
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp", summary="Verify OTP and get JWT token")
def verify_otp(otp_verify: OTPVerify, db: Session = Depends(get_db)):
    """
    Verifies the OTP and returns a JWT token if the OTP is valid.
    If the user does not exist, a new user is created.
    """
    if not verify_otp_util(db, otp_verify.phone_number, otp_verify.otp_code):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.phone_number == otp_verify.phone_number).first()
    if not user:
        user = User(phone_number=otp_verify.phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    role_name = user.role.name if user.role else "user"
    access_token = create_access_token(data={"sub": str(user.id), "role": role_name, "is_verified": user.verification_status == VerificationStatus.verified})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/lookup-otp", response_model=OTPAdminLookupResponse, summary="Lookup OTP for a phone number")
def lookup_otp(query: OTPAdminLookup = Depends(), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieves the most recent valid OTP for a phone number.
    Restricted to admin and owner roles.
    """
    db_otp = get_valid_otp(db, query.phone_number)
    if not db_otp:
        raise HTTPException(status_code=404, detail="No valid OTP found")

    return {
        "phone_number": db_otp.phone_number,
        "otp_code": db_otp.otp_code,
        "expires_at": db_otp.expires_at,
    }
