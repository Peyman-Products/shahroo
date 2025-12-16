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
    mime_type: Optional[str]
    size_bytes: Optional[int]
    checksum: Optional[str]
    uploaded_at: Optional[datetime]


class AdminKycSummary(BaseModel):
    status: VerificationStatus
    attempt_id: Optional[int] = None
    attempts_count: int
    id_card: Optional[AdminKycMedia] = None
    selfie: Optional[AdminKycMedia] = None
    last_decision: Optional[KycDecision] = None
