from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.wallet import Wallet as WalletSchema
from app.models.wallet import Wallet
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()

def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet

@router.get("/me", response_model=WalletSchema, summary="Get current user's wallet")
def read_user_wallet(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves the wallet of the currently authenticated user.
    """
    wallet = get_or_create_wallet(db, current_user.id)
    return wallet
