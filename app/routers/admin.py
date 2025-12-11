from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.user import User as UserSchema
from app.models.user import User, VerificationStatus
from app.utils.deps import get_current_user, user_has_permission
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskUpdate
from app.models.task import Task, TaskStep, TaskStatus
from app.models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus
from app.routers.wallet import get_or_create_wallet
from datetime import datetime, timezone

router = APIRouter()

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.role or current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

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

@router.post("/tasks", response_model=TaskSchema, summary="Create a new task", dependencies=[Depends(user_has_permission("create_task"))])
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Creates a new task. Only accessible by admin users with the 'create_task' permission.
    """
    db_task = Task(**task.model_dump(exclude={"steps"}))
    db_task.created_by_admin_id = current_user.id
    db.add(db_task)
    db.commit()
    for step_data in task.steps:
        db_step = TaskStep(**step_data.model_dump(), task_id=db_task.id)
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
    for field, value in task.model_dump(exclude_unset=True).items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task

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

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.earning,
        amount=db_task.price,
        status=TransactionStatus.confirmed,
        related_task_id=db_task.id,
        description=f"Earning from task #{db_task.id}"
    )
    db.add(transaction)

    wallet.balance += db_task.price

    db_task.status = TaskStatus.approved
    db_task.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(db_task)

    return db_task
