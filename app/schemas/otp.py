from pydantic import BaseModel

class OTPSend(BaseModel):
    phone_number: str

class OTPVerify(BaseModel):
    phone_number: str
    otp_code: str
