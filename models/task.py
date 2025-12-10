from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    OPEN = "open"
    DONE = "done"


class MessageType(str, Enum):
    EMAIL = "email"
    SLACK = "slack"


class Classification(str, Enum):
    TODO = "todo"
    FOLLOWUP = "followup"
    NOISE = "noise"


class IncomingMessage(BaseModel):
    """Input format from LLM/Prioritizer service"""
    id: str  # UUID from integrations service
    type: MessageType
    subject: Optional[str] = None
    sender: str
    classification: Classification
    task: str
    priority: int = Field(ge=1, le=5)


class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus = TaskStatus.OPEN
    due_at: Optional[datetime] = None
    priority: int = Field(ge=1, le=5)
    message_type: MessageType
    sender: str
    subject: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    task_id: int
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus
    due_at: Optional[datetime]
    priority: int
    message_type: MessageType
    sender: str
    subject: Optional[str]
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class TodoCreate(BaseModel):
    """Schema for creating a new todo"""
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus = TaskStatus.OPEN
    due_at: Optional[datetime] = None
    priority: int = Field(ge=1, le=5)
    message_type: MessageType
    sender: str
    subject: Optional[str] = None


class TodoResponse(BaseModel):
    """Schema for todo response"""
    todo_id: int
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus
    due_at: Optional[datetime]
    priority: int
    message_type: MessageType
    sender: str
    subject: Optional[str]
    created_at: datetime
    updated_at: datetime


class TodoUpdate(BaseModel):
    """Schema for updating a todo"""
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class FollowupCreate(BaseModel):
    """Schema for creating a new followup"""
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus = TaskStatus.OPEN
    due_at: Optional[datetime] = None
    priority: int = Field(ge=1, le=5)
    message_type: MessageType
    sender: str
    subject: Optional[str] = None


class FollowupResponse(BaseModel):
    """Schema for followup response"""
    followup_id: int
    user_id: int
    source_msg_id: str  # UUID from integrations service
    title: str
    status: TaskStatus
    due_at: Optional[datetime]
    priority: int
    message_type: MessageType
    sender: str
    subject: Optional[str]
    created_at: datetime
    updated_at: datetime


class FollowupUpdate(BaseModel):
    """Schema for updating a followup"""
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

