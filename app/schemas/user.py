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
    shaba_number: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    birthdate: Optional[date] = Field(None, example="1990-01-01")
    sex: Optional[str] = Field(None, example="Male")
    national_id: Optional[str] = Field(None, example="1234567890")
    shaba_number: Optional[str] = Field(None, example="IR820540102680020817909002")
    address: Optional[str] = Field(None, example="123 Main St")

from app.schemas.permission import Role

class User(UserBase):
    id: int
    id_card_image: Optional[str] = None
    selfie_image: Optional[str] = None
    verification_status: VerificationStatus
    role: Optional[Role] = None
    shaba_number: Optional[str] = None

    class Config:
        from_attributes = True
