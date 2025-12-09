from pydantic import BaseModel, Field
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
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    birthdate: Optional[date] = Field(None, example="1990-01-01")
    sex: Optional[str] = Field(None, example="Male")
    national_id: Optional[str] = Field(None, example="1234567890")
    address: Optional[str] = Field(None, example="123 Main St")

class User(UserBase):
    id: int
    id_card_image: Optional[str] = None
    selfie_image: Optional[str] = None
    verification_status: VerificationStatus
    role: str

    class Config:
        from_attributes = True
