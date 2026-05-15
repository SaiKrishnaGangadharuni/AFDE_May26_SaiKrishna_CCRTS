"""Business logic for complaint lifecycle, SLA calculation, history audit."""
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import (
    Complaint, ComplaintHistory, PriorityEnum, StatusEnum, SLA_HOURS, User, Notification
)


def generate_complaint_number(db: Session) -> str:
    """CMP-YYYYMMDD-XXXX (XXXX = 4 hex chars from a CSPRNG)."""
    today = datetime.utcnow().strftime("%Y%m%d")
    while True:
        suffix = secrets.token_hex(2).upper()  # 4 hex chars
        candidate = f"CMP-{today}-{suffix}"
        if not db.query(Complaint).filter(Complaint.complaint_number == candidate).first():
            return candidate


def compute_sla_due(priority: PriorityEnum, base: datetime | None = None) -> datetime:
    base = base or datetime.utcnow()
    return base + timedelta(hours=SLA_HOURS[priority])


def log_history(
    db: Session,
    complaint: Complaint,
    actor: User,
    action: str,
    old_status: StatusEnum | None = None,
    new_status: StatusEnum | None = None,
    comment: str | None = None,
) -> ComplaintHistory:
    entry = ComplaintHistory(
        complaint_id=complaint.id,
        updated_by=actor.id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    db.add(entry)
    return entry


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    complaint_id: int | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        complaint_id=complaint_id,
    )
    db.add(notif)
    return notif


def refresh_sla_breach(complaint: Complaint) -> None:
    """Mark SLA as breached if the due-time has passed and the complaint is still open."""
    open_states = {
        StatusEnum.OPEN, StatusEnum.ASSIGNED, StatusEnum.IN_PROGRESS,
        StatusEnum.PENDING_CUSTOMER, StatusEnum.ESCALATED, StatusEnum.REOPENED,
    }
    if complaint.status in open_states and datetime.utcnow() > complaint.sla_due_at:
        complaint.sla_breached = True


# Permissible transitions — guards state-machine integrity.
ALLOWED_TRANSITIONS: dict[StatusEnum, set[StatusEnum]] = {
    StatusEnum.OPEN: {StatusEnum.ASSIGNED, StatusEnum.IN_PROGRESS, StatusEnum.ESCALATED, StatusEnum.CLOSED},
    StatusEnum.ASSIGNED: {StatusEnum.IN_PROGRESS, StatusEnum.PENDING_CUSTOMER, StatusEnum.ESCALATED, StatusEnum.RESOLVED, StatusEnum.CLOSED},
    StatusEnum.IN_PROGRESS: {StatusEnum.PENDING_CUSTOMER, StatusEnum.ESCALATED, StatusEnum.RESOLVED, StatusEnum.CLOSED},
    StatusEnum.PENDING_CUSTOMER: {StatusEnum.IN_PROGRESS, StatusEnum.ESCALATED, StatusEnum.RESOLVED, StatusEnum.CLOSED},
    StatusEnum.ESCALATED: {StatusEnum.IN_PROGRESS, StatusEnum.RESOLVED, StatusEnum.CLOSED},
    StatusEnum.RESOLVED: {StatusEnum.CLOSED, StatusEnum.REOPENED},
    StatusEnum.CLOSED: {StatusEnum.REOPENED},
    StatusEnum.REOPENED: {StatusEnum.ASSIGNED, StatusEnum.IN_PROGRESS, StatusEnum.ESCALATED, StatusEnum.RESOLVED, StatusEnum.CLOSED},
}


def can_transition(current: StatusEnum, target: StatusEnum) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())
