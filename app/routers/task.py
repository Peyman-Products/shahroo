from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskUpdate, TaskStepUpdate
from app.models.task import Task, TaskStep, TaskStatus, StepStatus
from app.models.user import User, VerificationStatus
from app.utils.deps import get_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", response_model=List[TaskSchema], summary="Get all tasks")
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of all tasks.
    """
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskSchema, summary="Get a specific task")
def read_task(task_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific task by its ID.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.post("/{task_id}/accept", response_model=TaskSchema, summary="Accept a task")
def accept_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Accepts a task.
    """
    if current_user.verification_status != VerificationStatus.verified:
        raise HTTPException(status_code=403, detail="User is not verified")

    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.status != TaskStatus.issued or db_task.assigned_user_id is not None:
        raise HTTPException(status_code=400, detail="Task cannot be accepted")

    db_task.assigned_user_id = current_user.id
    db_task.status = TaskStatus.in_progress
    db_task.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.post("/{task_id}/complete", response_model=TaskSchema, summary="Complete a task")
def complete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Marks a task as complete.
    """
    db_task = db.query(Task).filter(Task.id == task_id, Task.assigned_user_id == current_user.id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found or not assigned to user")

    for step in db_task.steps:
        if step.status != StepStatus.done:
            raise HTTPException(status_code=400, detail="All steps must be completed")

    db_task.status = TaskStatus.done
    db_task.done_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.patch("/{task_id}/steps/{step_id}", response_model=TaskSchema, summary="Update a task step")
def update_task_step(task_id: int, step_id: int, step: TaskStepUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Updates a specific task step.
    """
    db_task = db.query(Task).filter(Task.id == task_id, Task.assigned_user_id == current_user.id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found or not assigned to user")

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
