from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from app.db import Base
import enum

class TaskStatus(enum.Enum):
    issued = "issued"
    in_progress = "in_progress"
    done = "done"
    approved = "approved"
    canceled = "canceled"
    failed = "failed"
    rejected = "rejected"

class StepStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"
    canceled = "canceled"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    price = Column(Float)
    estimated_time = Column(Integer) # in minutes
    start_datetime = Column(DateTime(timezone=True))
    status = Column(Enum(TaskStatus), default=TaskStatus.issued)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    done_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business")
    assigned_user = relationship("User")
    steps = relationship("TaskStep", back_populates="task")

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    title = Column(String)
    description = Column(String, nullable=True)
    address = Column(String)
    status = Column(Enum(StepStatus), default=StepStatus.pending)
    order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="steps")
