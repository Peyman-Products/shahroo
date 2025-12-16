from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.models.user import VerificationStatus
from app.schemas.kyc import KycDecision

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
from app.schemas.kyc import AdminKycSummary
from typing import List


class User(UserBase):
    id: int
    verification_status: VerificationStatus
    role: Optional[Role] = None
    shaba_number: Optional[str] = None
    avatar_url: Optional[str] = None
    id_card_url: Optional[str] = None
    selfie_url: Optional[str] = None
    last_decision: Optional[KycDecision] = None

    class Config:
        from_attributes = True


class AdminUser(User):
    kyc: Optional[AdminKycSummary] = None


class VerificationDecisionPayload(BaseModel):
    status: VerificationStatus
    reason_codes: Optional[List[str]] = None
    reason_text: Optional[str] = None
    allow_resubmission: bool = True
