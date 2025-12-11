from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.user import User as UserSchema
from app.models.user import User, VerificationStatus
from app.utils.deps import get_current_user, user_has_permission
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskStepCreate, TaskStepUpdate, TaskUpdate, TaskKind as TaskKindSchema, TaskKindCreate
from app.models.task import Task, TaskStep, TaskStatus, StepStatus
from app.models.task_meta import TaskKind
from app.models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus
from app.schemas.wallet import WalletTransaction as WalletTransactionSchema
from app.routers.wallet import get_or_create_wallet
from app.utils.wallet import refresh_wallet_balance
from datetime import datetime, timezone
from app.schemas.otp import OTPAdminLookup, OTPAdminLookupResponse
from app.utils.otp import get_valid_otp

router = APIRouter()

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

@router.patch("/users/{user_id}/verification", response_model=UserSchema, summary="Update user verification status")
def update_user_verification(user_id: int, status: VerificationStatus, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Updates the verification status of a user. Only accessible by admin users.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.verification_status = status
    db.commit()
    db.refresh(db_user)
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


@router.get("/wallets/checkout-requests", response_model=List[WalletTransactionSchema], summary="List wallet checkout requests")
def list_checkout_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Retrieve payout transactions that are awaiting approval by an admin user.
    """

    return (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.type == TransactionType.payout,
            WalletTransaction.status == TransactionStatus.requested,
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
    Confirm a payout request and apply it to the user's wallet balance. The payout
    must still be covered by the confirmed balance after accounting for other
    pending or requested payouts.
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

    if transaction.status not in {TransactionStatus.requested, TransactionStatus.pending}:
        raise HTTPException(status_code=400, detail="Transaction is not awaiting approval")

    wallet = transaction.wallet or get_or_create_wallet(db, transaction.wallet_id)
    refresh_wallet_balance(db, wallet)

    reserved_amount = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.type == TransactionType.payout,
            WalletTransaction.status.in_([TransactionStatus.requested, TransactionStatus.pending]),
            WalletTransaction.id != transaction.id,
        )
        .scalar()
    )

    available_balance = wallet.balance - reserved_amount

    if transaction.amount > available_balance:
        raise HTTPException(status_code=400, detail="Insufficient available balance to approve checkout")

    transaction.status = TransactionStatus.confirmed

    db.flush()
    refresh_wallet_balance(db, wallet, commit=False)
    db.commit()
    db.refresh(transaction)
    db.refresh(wallet)

    return transaction
