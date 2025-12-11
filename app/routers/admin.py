from fastapi import APIRouter, Depends, HTTPException, Response
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
