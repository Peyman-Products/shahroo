from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, StepStatus

class TaskStepBase(BaseModel):
    title: str
    description: Optional[str] = None
    address: str
    order: int

class TaskStepCreate(TaskStepBase):
    pass

class TaskStepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    status: Optional[StepStatus] = None
    order: Optional[int] = None

class TaskStep(TaskStepBase):
    id: int
    task_id: int
    status: StepStatus
    done_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    title: str
    business_id: int
    price: float
    estimated_time: int
    start_datetime: datetime

class TaskCreate(TaskBase):
    steps: List[TaskStepCreate] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    business_id: Optional[int] = None
    price: Optional[float] = None
    estimated_time: Optional[int] = None
    start_datetime: Optional[datetime] = None
    status: Optional[TaskStatus] = None

class Task(TaskBase):
    id: int
    assigned_user_id: Optional[int] = None
    status: TaskStatus
    steps: List[TaskStep] = []
    accepted_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        orm_mode = True
