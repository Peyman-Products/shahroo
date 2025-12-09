from pydantic import BaseModel, Field

class OTPSend(BaseModel):
    phone_number: str = Field(..., example="0922171380")

class OTPVerify(BaseModel):
    phone_number: str = Field(..., example="0922171380")
    otp_code: str = Field(..., example="123456")
