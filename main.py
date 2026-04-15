from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, Integer, String, Text, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column


# -----------------------------
# DATABASE SETUP
# -----------------------------

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# -----------------------------
# DATABASE MODEL
# -----------------------------

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String, default="medium")
    status: Mapped[str] = mapped_column(String, default="open")
    assignee: Mapped[str] = mapped_column(String, default="unassigned")
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


Base.metadata.create_all(bind=engine)


# -----------------------------
# PYDANTIC SCHEMAS
# -----------------------------

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"open", "in-progress", "complete"}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    status: Optional[str] = "open"
    assignee: Optional[str] = "unassigned"
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in VALID_PRIORITIES:
            raise ValueError("Priority must be low, medium, or high")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in VALID_STATUSES:
            raise ValueError("Status must be open, in-progress, or complete")
        return value

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value if value else "unassigned"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in VALID_PRIORITIES:
            raise ValueError("Priority must be low, medium, or high")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in VALID_STATUSES:
            raise ValueError("Status must be open, in-progress, or complete")
        return value

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value if value else "unassigned"


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    assignee: str
    due_date: Optional[date]

    class Config:
        from_attributes = True


# -----------------------------
# FASTAPI APP
# -----------------------------

app = FastAPI(title="Task & Workflow API")


# -----------------------------
# ROUTES
# -----------------------------

@app.get("/")
def home():
    return {"message": "Task & Workflow API is running"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate):
    db = SessionLocal()

    new_task = Task(
        title=task.title,
        description=task.description or "",
        priority=task.priority or "medium",
        status=task.status or "open",
        assignee=task.assignee or "unassigned",
        due_date=task.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()

    return new_task


@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks():
    db = SessionLocal()
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    db.close()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    db.close()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated_task: TaskUpdate):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")

    if updated_task.title is not None:
        task.title = updated_task.title

    if updated_task.description is not None:
        task.description = updated_task.description

    if updated_task.priority is not None:
        task.priority = updated_task.priority

    if updated_task.status is not None:
        task.status = updated_task.status

    if updated_task.assignee is not None:
        task.assignee = updated_task.assignee

    if updated_task.due_date is not None:
        task.due_date = updated_task.due_date

    db.commit()
    db.refresh(task)
    db.close()

    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    db.close()

    return {"message": f"Task {task_id} deleted successfully"}


@app.get("/tasks/status/{status}", response_model=List[TaskResponse])
def get_tasks_by_status(status: str):
    status = status.strip().lower()

    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Status must be open, in-progress, or complete"
        )

    db = SessionLocal()
    tasks = db.query(Task).filter(Task.status == status).order_by(Task.id.desc()).all()
    db.close()

    return tasks


@app.get("/tasks/priority/{priority}", response_model=List[TaskResponse])
def get_tasks_by_priority(priority: str):
    priority = priority.strip().lower()

    if priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Priority must be low, medium, or high"
        )

    db = SessionLocal()
    tasks = db.query(Task).filter(Task.priority == priority).order_by(Task.id.desc()).all()
    db.close()

    return tasks