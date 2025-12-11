from sqlalchemy.orm import Session

from app.models.wallet import Wallet, WalletTransaction, TransactionStatus, TransactionType


def refresh_wallet_balance(db: Session, wallet: Wallet, commit: bool = True) -> Wallet:
    """
    Recalculate a wallet's balance using confirmed transactions. Earnings and adjustments
    increase the balance, while payouts decrease it. This keeps the balance tied to
    relational transaction data so changes can be reversed by updating transactions.
    """

    confirmed_like_statuses = {
        TransactionStatus.confirmed,
        TransactionStatus.in_progress,
        TransactionStatus.sent_to_bank,
        TransactionStatus.paid,
    }

    transactions = (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.status.in_(confirmed_like_statuses),
        )
        .all()
    )

    balance = 0.0
    for transaction in transactions:
        if transaction.type in {TransactionType.earning, TransactionType.adjustment}:
            balance += transaction.amount
        elif transaction.type == TransactionType.payout:
            balance -= transaction.amount

    wallet.balance = balance

    if commit:
        db.commit()
        db.refresh(wallet)

    return wallet
