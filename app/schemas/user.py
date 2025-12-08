from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.models.user import VerificationStatus

class UserBase(BaseModel):
    phone_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[date] = None
    sex: Optional[str] = None
    national_id: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[date] = None
    sex: Optional[str] = None
    national_id: Optional[str] = None
    address: Optional[str] = None

class User(UserBase):
    id: int
    id_card_image: Optional[str] = None
    selfie_image: Optional[str] = None
    verification_status: VerificationStatus
    role: str

    class Config:
        orm_mode = True
