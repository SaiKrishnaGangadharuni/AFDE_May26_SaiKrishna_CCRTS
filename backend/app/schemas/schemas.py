"""Pydantic v2 schemas for request validation and response serialization."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from ..models import PriorityEnum, StatusEnum


# ---------------------------------------------------------------------------
# Auth & user
# ---------------------------------------------------------------------------
class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)


class UserRegister(UserBase):
    password: str = Field(min_length=6, max_length=128)
    # On public registration we always create Customers. Admin can create other roles via /users.
    role_name: Optional[str] = "Customer"


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role_id: int


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    role: RoleOut
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6, max_length=128)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(CategoryBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------
class ComplaintCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    category_id: int
    priority: PriorityEnum = PriorityEnum.MEDIUM


class ComplaintUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None


class ComplaintAssign(BaseModel):
    agent_id: int


class ComplaintStatusUpdate(BaseModel):
    status: StatusEnum
    comment: Optional[str] = None


class ComplaintEscalate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ComplaintResolve(BaseModel):
    resolution_notes: str = Field(min_length=3)


class ComplaintReopen(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AttachmentOut(BaseModel):
    id: int
    file_name: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HistoryOut(BaseModel):
    id: int
    action: str
    old_status: Optional[StatusEnum] = None
    new_status: Optional[StatusEnum] = None
    comment: Optional[str] = None
    updated_at: datetime
    updated_by_user: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = None


class FeedbackOut(FeedbackCreate):
    id: int
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ComplaintOut(BaseModel):
    id: int
    complaint_number: str
    subject: str
    description: str
    priority: PriorityEnum
    status: StatusEnum
    sla_due_at: datetime
    sla_breached: bool
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    escalation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    customer: UserOut
    assigned_agent: Optional[UserOut] = None
    category: CategoryOut
    attachments: List[AttachmentOut] = []
    feedback: Optional[FeedbackOut] = None
    model_config = ConfigDict(from_attributes=True)


class ComplaintListOut(BaseModel):
    """Lightweight projection used by list endpoints."""
    id: int
    complaint_number: str
    subject: str
    priority: PriorityEnum
    status: StatusEnum
    sla_due_at: datetime
    sla_breached: bool
    created_at: datetime
    customer_name: str
    assigned_agent_name: Optional[str] = None
    category_name: str


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    complaint_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Dashboard / Analytics
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_complaints: int
    open: int
    in_progress: int
    pending_customer: int
    escalated: int
    resolved: int
    closed: int
    reopened: int
    sla_breaches: int
    avg_resolution_hours: Optional[float] = None


class AgentPerformance(BaseModel):
    agent_id: int
    agent_name: str
    total_assigned: int
    resolved: int
    avg_resolution_hours: Optional[float] = None
    sla_breaches: int


class CategoryStats(BaseModel):
    category_id: int
    category_name: str
    total: int


class TrendPoint(BaseModel):
    period: str       # e.g. "2026-05"
    total: int
    resolved: int
