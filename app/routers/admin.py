from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db import get_db
from app.schemas.user import User as UserSchema, AdminUser, VerificationDecisionPayload
from app.schemas.kyc import AdminKycSummary, AdminKycMedia, KycDecision
from app.models.user import User, VerificationStatus
from app.utils.media import MediaManager
from app.models.kyc import KycAttempt
from app.utils.deps import get_current_user, user_has_permission
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskStepCreate, TaskStepUpdate, TaskUpdate, TaskKind as TaskKindSchema, TaskKindCreate
from app.models.task import Task, TaskStep, TaskStatus, StepStatus
from app.models.task_meta import TaskKind
from app.models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus
from app.schemas.wallet import WalletAdminSummary, WalletTransaction as WalletTransactionSchema
from app.routers.wallet import get_or_create_wallet
from app.utils.wallet import refresh_wallet_balance
from datetime import datetime, timezone
from app.schemas.otp import OTPAdminLookup, OTPAdminLookupResponse
from app.utils.otp import get_valid_otp

router = APIRouter()
media_manager = MediaManager()


def _parse_codes(codes: Optional[str]) -> Optional[List[str]]:
    if not codes:
        return None
    return [code for code in codes.split(",") if code]


def _media_to_admin(path: str | None) -> Optional[AdminKycMedia]:
    if not path:
        return None
    return AdminKycMedia(url=media_manager.url_for(path))


def _admin_last_decision(user: User, attempt: Optional[KycAttempt]) -> Optional[KycDecision]:
    if user.kyc_last_decided_at:
        return KycDecision(
            status=user.verification_status,
            reason_codes=_parse_codes(user.kyc_last_reason_codes),
            reason_text=user.kyc_last_reason_text,
            decided_at=user.kyc_last_decided_at,
        )
    if attempt and attempt.decided_at:
        return KycDecision(
            status=attempt.status,
            reason_codes=_parse_codes(attempt.reason_codes),
            reason_text=attempt.reason_text,
            decided_at=attempt.decided_at,
        )
    return None


def _build_admin_kyc_summary(user: User) -> AdminKycSummary:
    attempt = user.current_kyc_attempt
    return AdminKycSummary(
        status=user.verification_status if user.verification_status != VerificationStatus.unverified else (attempt.status if attempt else VerificationStatus.unverified),
        attempt_id=attempt.id if attempt else None,
        attempts_count=len(user.kyc_attempts) if user.kyc_attempts else (1 if attempt else 0),
        id_card=_media_to_admin(user.id_card_image),
        selfie=_media_to_admin(user.selfie_image),
        last_decision=_admin_last_decision(user, attempt),
    )

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.role or current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


@router.get("/otp", response_model=OTPAdminLookupResponse, summary="Lookup OTP for a phone number")
def lookup_otp(query: OTPAdminLookup = Depends(), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_otp = get_valid_otp(db, query.phone_number)
    if not db_otp:
        raise HTTPException(status_code=404, detail="No valid OTP found")
    return {
        "phone_number": db_otp.phone_number,
        "otp_code": db_otp.otp_code,
        "expires_at": db_otp.expires_at,
    }

@router.get("/users", response_model=List[UserSchema], summary="Get all users")
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieves a list of all users. Only accessible by admin users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=AdminUser, summary="Get user with KYC media")
def read_user_detail(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.kyc = _build_admin_kyc_summary(db_user)
    db_user.last_decision = _admin_last_decision(db_user, db_user.current_kyc_attempt)
    return db_user

@router.patch("/users/{user_id}/verification", response_model=AdminUser, summary="Update user verification status")
def update_user_verification(user_id: int, payload: VerificationDecisionPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Updates the verification status of a user. Only accessible by admin users.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.status == VerificationStatus.pending:
        raise HTTPException(status_code=400, detail="Pending status is managed automatically by uploads")

    attempt = db_user.current_kyc_attempt
    if attempt is None:
        attempt = KycAttempt(user_id=db_user.id, status=db_user.verification_status)
        db.add(attempt)
        db.flush()
        db_user.current_kyc_attempt_id = attempt.id

    now = datetime.now(timezone.utc)

    if payload.status == VerificationStatus.verified:
        if not db_user.id_card_image or not db_user.selfie_image:
            raise HTTPException(status_code=400, detail="KYC media is required before verification")
        attempt.status = VerificationStatus.verified
        attempt.decided_at = now
        attempt.allow_resubmission = False
        db_user.verification_status = VerificationStatus.verified
        db_user.kyc_locked_at = now
        db_user.kyc_last_reason_codes = None
        db_user.kyc_last_reason_text = None
        db_user.kyc_last_decided_at = now
    elif payload.status == VerificationStatus.unverified:
        if attempt.status == VerificationStatus.verified:
            attempt = KycAttempt(user_id=db_user.id, status=VerificationStatus.unverified, allow_resubmission=True)
            db.add(attempt)
            db.flush()
            db_user.current_kyc_attempt_id = attempt.id
        else:
            attempt.status = VerificationStatus.unverified
            attempt.decided_at = None
            attempt.reason_codes = None
            attempt.reason_text = None
            attempt.allow_resubmission = True

        db_user.verification_status = VerificationStatus.unverified
        db_user.kyc_locked_at = None
        db_user.kyc_last_reason_codes = None
        db_user.kyc_last_reason_text = None
        db_user.kyc_last_decided_at = None
    elif payload.status == VerificationStatus.rejected:
        attempt.status = VerificationStatus.rejected
        attempt.reason_codes = ",".join(payload.reason_codes) if payload.reason_codes else None
        attempt.reason_text = payload.reason_text
        attempt.decided_at = now
        attempt.allow_resubmission = payload.allow_resubmission
        db_user.verification_status = VerificationStatus.rejected
        db_user.kyc_locked_at = None
        db_user.kyc_last_reason_codes = attempt.reason_codes
        db_user.kyc_last_reason_text = payload.reason_text
        db_user.kyc_last_decided_at = now
    else:
        db_user.verification_status = payload.status

    db.commit()
    db.refresh(db_user)
    db_user.kyc = _build_admin_kyc_summary(db_user)
    db_user.last_decision = _admin_last_decision(db_user, attempt)
    return db_user


@router.get("/task-kinds", response_model=List[TaskKindSchema], summary="Get all task kinds")
def list_task_kinds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Retrieves available task kinds for use in task creation."""
    return db.query(TaskKind).offset(skip).limit(limit).all()


@router.post("/task-kinds", response_model=TaskKindSchema, summary="Create a new task kind")
def create_task_kind(kind: TaskKindCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Creates a new task kind to categorize tasks from the admin panel."""
    existing = db.query(TaskKind).filter(TaskKind.name == kind.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Task kind with this name already exists")
    db_kind = TaskKind(**kind.dict())
    db.add(db_kind)
    db.commit()
    db.refresh(db_kind)
    return db_kind

@router.post("/tasks", response_model=TaskSchema, summary="Create a new task", dependencies=[Depends(user_has_permission("create_task"))])
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Creates a new task. Only accessible by admin users with the 'create_task' permission.
    """
    db_task = Task(**task.dict(exclude={"steps"}), created_by_admin_id=current_user.id)
    db.add(db_task)
    db.commit()
    for step_data in task.steps:
        db_step = TaskStep(**step_data.dict(), task_id=db_task.id)
        db.add(db_step)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[TaskSchema], summary="List tasks with assigned user info")
def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieves tasks for admin users, including assigned user details and task steps.
    """
    tasks = (
        db.query(Task)
        .options(joinedload(Task.assigned_user), joinedload(Task.steps))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks

@router.get("/tasks/{task_id}", response_model=TaskSchema, summary="Get task details with assigned user info")
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieves a specific task along with assigned user details and task steps.
    """
    db_task = (
        db.query(Task)
        .options(joinedload(Task.assigned_user), joinedload(Task.steps))
        .filter(Task.id == task_id)
        .first()
    )
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.patch("/tasks/{task_id}", response_model=TaskSchema, summary="Update a task")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Updates a specific task. Only accessible by admin users.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in task.dict(exclude_unset=True).items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Deletes a specific task along with its steps. Only accessible by admin users.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.query(TaskStep).filter(TaskStep.task_id == task_id).delete(synchronize_session=False)
    db.delete(db_task)
    db.commit()
    return Response(status_code=204)


@router.post("/tasks/{task_id}/steps", response_model=TaskSchema, summary="Add a step to a task")
def add_task_step(task_id: int, step: TaskStepCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Adds a new step to a task. Only accessible by admin users.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db_step = TaskStep(**step.dict(), task_id=task_id)
    db.add(db_step)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.patch("/tasks/{task_id}/steps/{step_id}", response_model=TaskSchema, summary="Update a task step")
def update_task_step(task_id: int, step_id: int, step: TaskStepUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Updates a specific task step. Only accessible by admin users.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db_step = db.query(TaskStep).filter(TaskStep.id == step_id, TaskStep.task_id == task_id).first()
    if db_step is None:
        raise HTTPException(status_code=404, detail="Step not found")

    for field, value in step.dict(exclude_unset=True).items():
        setattr(db_step, field, value)

    if db_step.status == StepStatus.done and db_step.done_at is None:
        db_step.done_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/tasks/{task_id}/steps/{step_id}", status_code=204, summary="Delete a task step")
def delete_task_step(task_id: int, step_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Deletes a specific step from a task. Only accessible by admin users.
    """
    db_step = db.query(TaskStep).filter(TaskStep.id == step_id, TaskStep.task_id == task_id).first()
    if db_step is None:
        raise HTTPException(status_code=404, detail="Step not found")

    db.delete(db_step)
    db.commit()
    return Response(status_code=204)

@router.post("/tasks/{task_id}/approve", response_model=TaskSchema, summary="Approve a completed task")
def approve_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Approves a completed task and credits the user's wallet. Only accessible by admin users.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if db_task.status != TaskStatus.done:
        raise HTTPException(status_code=400, detail="Task is not marked as done")

    if db_task.assigned_user_id is None:
        raise HTTPException(status_code=400, detail="Task has no assigned user")

    wallet = get_or_create_wallet(db, db_task.assigned_user_id)

    existing_transaction = (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.related_task_id == db_task.id,
            WalletTransaction.type == TransactionType.earning,
            WalletTransaction.status == TransactionStatus.confirmed,
        )
        .first()
    )

    if existing_transaction:
        raise HTTPException(status_code=400, detail="Task earning already processed")

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.earning,
        amount=db_task.price,
        status=TransactionStatus.confirmed,
        related_task_id=db_task.id,
        description=f"Earning from task #{db_task.id}"
    )
    db.add(transaction)

    db_task.status = TaskStatus.approved
    db_task.approved_at = datetime.now(timezone.utc)

    db.flush()
    refresh_wallet_balance(db, wallet, commit=False)
    db.commit()

    db.refresh(db_task)
    db.refresh(wallet)

    return db_task


# Wallet cashout management


@router.get("/wallets", response_model=List[WalletAdminSummary], summary="List wallets with cashout info")
def list_wallets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Return wallets along with balances and active cashout requests."""

    wallets = db.query(Wallet).offset(skip).limit(limit).all()

    summaries: List[WalletAdminSummary] = []
    for wallet in wallets:
        refresh_wallet_balance(db, wallet, commit=False)
        active_cashouts = [
            tx
            for tx in wallet.transactions
            if tx.type == TransactionType.payout
            and tx.status in {TransactionStatus.in_progress, TransactionStatus.sent_to_bank}
        ]
        summaries.append(
            WalletAdminSummary(
                id=wallet.id,
                user_id=wallet.user_id,
                balance=wallet.balance,
                shaba_number=wallet.user.shaba_number if wallet.user else None,
                active_cashouts=active_cashouts,
            )
        )

    return summaries


@router.get("/wallets/checkout-requests", response_model=List[WalletTransactionSchema], summary="List wallet checkout requests")
def list_checkout_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieve payout transactions that are awaiting approval by an admin user.
    """

    return (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.type == TransactionType.payout,
            WalletTransaction.status.in_(
                [TransactionStatus.requested, TransactionStatus.sent_to_bank]
            ),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post(
    "/wallets/checkout-requests/{transaction_id}/approve",
    response_model=WalletTransactionSchema,
    summary="Approve a wallet checkout request",
)
def approve_checkout_request(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Approve a payout request and move it forward to bank processing.
    """

    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(status_code=404, detail="Checkout request not found")

    if transaction.type != TransactionType.payout:
        raise HTTPException(status_code=400, detail="Transaction is not a payout request")

    if transaction.status != TransactionStatus.requested:
        raise HTTPException(status_code=400, detail="Transaction is not awaiting approval")

    wallet = transaction.wallet or get_or_create_wallet(db, transaction.wallet_id)
    refresh_wallet_balance(db, wallet)

    transaction.status = TransactionStatus.sent_to_bank

    db.flush()
    refresh_wallet_balance(db, wallet, commit=False)
    db.commit()
    db.refresh(transaction)
    db.refresh(wallet)

    return transaction


@router.post(
    "/wallets/checkout-requests/{transaction_id}/complete",
    response_model=WalletTransactionSchema,
    summary="Mark a wallet checkout as paid by the bank",
)
def complete_checkout_request(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Finalize a payout after the bank confirms payment."""

    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(status_code=404, detail="Checkout request not found")

    if transaction.type != TransactionType.payout:
        raise HTTPException(status_code=400, detail="Transaction is not a payout request")

    if transaction.status != TransactionStatus.sent_to_bank:
        raise HTTPException(status_code=400, detail="Transaction is not awaiting bank confirmation")

    transaction.status = TransactionStatus.paid

    wallet = transaction.wallet or get_or_create_wallet(db, transaction.wallet_id)

    db.flush()
    refresh_wallet_balance(db, wallet, commit=False)
    db.commit()
    db.refresh(transaction)
    db.refresh(wallet)

    return transaction


@router.post(
    "/wallets/checkout-requests/{transaction_id}/deny",
    response_model=WalletTransactionSchema,
    summary="Deny a wallet checkout request",
)
def deny_checkout_request(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Reject a payout request and return the funds to the user's wallet."""

    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(status_code=404, detail="Checkout request not found")

    if transaction.type != TransactionType.payout:
        raise HTTPException(status_code=400, detail="Transaction is not a payout request")

    if transaction.status not in {TransactionStatus.requested, TransactionStatus.sent_to_bank}:
        raise HTTPException(status_code=400, detail="Transaction is not eligible for denial")

    transaction.status = TransactionStatus.denied
    wallet = transaction.wallet or get_or_create_wallet(db, transaction.wallet_id)

    db.flush()
    refresh_wallet_balance(db, wallet, commit=False)
    db.commit()
    db.refresh(transaction)
    db.refresh(wallet)

    return transaction
