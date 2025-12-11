from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db import Base
import enum

class TransactionType(enum.Enum):
    earning = "earning"
    payout = "payout"
    adjustment = "adjustment"

class TransactionStatus(enum.Enum):
    requested = "requested"
    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"
    in_progress = "in_progress"
    sent_to_bank = "sent_to_bank"
    paid = "paid"
    denied = "denied"

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    transactions = relationship("WalletTransaction", back_populates="wallet")

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    type = Column(Enum(TransactionType))
    amount = Column(Float)
    status = Column(Enum(TransactionStatus))
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")
    related_task = relationship("Task")
