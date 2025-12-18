from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.user import VerificationStatus


class KycDecision(BaseModel):
    status: VerificationStatus
    reason_codes: Optional[List[str]] = None
    reason_text: Optional[str] = None
    decided_at: Optional[datetime] = None


class KycStatusResponse(BaseModel):
    verification_status: VerificationStatus
    last_decision: Optional[KycDecision] = None
    can_upload_kyc: bool


class AdminKycMedia(BaseModel):
    url: str


class AdminKycSummary(BaseModel):
    status: VerificationStatus
    attempt_id: Optional[int] = None
    attempts_count: int
    id_card: Optional[AdminKycMedia] = None
    selfie: Optional[AdminKycMedia] = None
    last_decision: Optional[KycDecision] = None


class KycMedia(BaseModel):
    file_name: str
    url: str


class KycMediaUploadResponse(BaseModel):
    status: VerificationStatus
    id_card: KycMedia
    selfie: KycMedia


class KycMediaStatusResponse(BaseModel):
    status: VerificationStatus
    message: str
    id_card: Optional[KycMedia] = None
    selfie: Optional[KycMedia] = None
