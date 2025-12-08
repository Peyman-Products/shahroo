from pydantic import BaseModel
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

    class Config:
        orm_mode = True

class WalletBase(BaseModel):
    balance: float

class Wallet(WalletBase):
    id: int
    user_id: int
    transactions: List[WalletTransaction] = []

    class Config:
        orm_mode = True
