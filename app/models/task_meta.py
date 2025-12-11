from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

# Association Table for Task and TaskTag
task_tag_link = Table('task_tag_link', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('task_tags.id'), primary_key=True)
)

class TaskCategory(Base):
    __tablename__ = "task_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    tasks = relationship("Task", back_populates="category")


class TaskKind(Base):
    __tablename__ = "task_kinds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    tasks = relationship("Task", back_populates="kind")

class TaskTag(Base):
    __tablename__ = "task_tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    tasks = relationship("Task", secondary=task_tag_link, back_populates="tags")

class TaskMeta(Base):
    __tablename__ = "task_meta"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String)
    value = Column(String)
    task_id = Column(Integer, ForeignKey("tasks.id"))
