from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.wallet import TransactionType, TransactionStatus

class WalletTransactionBase(BaseModel):
    type: TransactionType
    amount: float
    status: TransactionStatus
    related_task_id: Optional[int] = None
    description: Optional[str] = None

class WalletTransactionCreate(WalletTransactionBase):
    pass

class WalletTransaction(WalletTransactionBase):
    id: int
    wallet_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WalletBase(BaseModel):
    balance: float
    shaba_number: Optional[str] = None

class Wallet(WalletBase):
    id: int
    user_id: int
    transactions: List[WalletTransaction] = []

    model_config = ConfigDict(from_attributes=True)


class WalletCheckoutRequest(BaseModel):
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class WalletAdminSummary(WalletBase):
    id: int
    user_id: int
    active_cashouts: List[WalletTransaction] = []

    model_config = ConfigDict(from_attributes=True)
