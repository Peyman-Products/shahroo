import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from kavenegar import *
from app.core.config import settings
from app.models.otp import OTP

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp(db: Session, phone_number: str):
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

    db_otp = OTP(phone_number=phone_number, otp_code=otp_code, expires_at=expires_at)
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)

    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'receptor': phone_number,
            'template': settings.KAVENEGAR_OTP_TEMPLATE,
            'token': otp_code,
            'type': 'sms',
        }
        response = api.verify_lookup(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)

    return db_otp

def verify_otp(db: Session, phone_number: str, otp_code: str):
    db_otp = db.query(OTP).filter(
        OTP.phone_number == phone_number,
        OTP.otp_code == otp_code,
        OTP.used == False,
        OTP.expires_at > datetime.now(timezone.utc)
    ).first()

    if db_otp:
        db_otp.used = True
        db.commit()
        return True
    return False


def get_valid_otp(db: Session, phone_number: str):
    return db.query(OTP).filter(
        OTP.phone_number == phone_number,
        OTP.used == False,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.expires_at.desc()).first()
