from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.wallet import Wallet as WalletSchema
from app.models.wallet import Wallet
from app.models.user import User
from app.utils.deps import get_current_user
from app.utils.wallet import refresh_wallet_balance

router = APIRouter()

def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet

from app.schemas.wallet import WalletTransaction as WalletTransactionSchema
from app.models.wallet import WalletTransaction
from typing import List

@router.get("/me", response_model=WalletSchema, summary="Get current user's wallet")
def read_user_wallet(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves the wallet of the currently authenticated user.
    """
    wallet = get_or_create_wallet(db, current_user.id)
    refresh_wallet_balance(db, wallet)
    return wallet

@router.get("/me/transactions", response_model=List[WalletTransactionSchema], summary="Get current user's wallet transactions")
def read_user_wallet_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves the wallet transactions of the currently authenticated user.
    """
    wallet = get_or_create_wallet(db, current_user.id)
    refresh_wallet_balance(db, wallet)
    transactions = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet.id).offset(skip).limit(limit).all()
    return transactions
