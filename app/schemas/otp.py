from pydantic import BaseModel, Field, validator
from app.utils.helpers import normalize_phone_number

class OTPSend(BaseModel):
    phone_number: str = Field(..., example="09220171380")

    @validator("phone_number")
    def validate_phone_number(cls, v):
        return normalize_phone_number(v)

class OTPVerify(BaseModel):
    phone_number: str = Field(..., example="09220171380")
    otp_code: str = Field(..., example="123456")

    @validator("phone_number")
    def validate_phone_number(cls, v):
        return normalize_phone_number(v)
