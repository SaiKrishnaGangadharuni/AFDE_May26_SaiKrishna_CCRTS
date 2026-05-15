"""Complaint endpoints — registration, listing, search/filter, assignment,
status transitions, escalation, resolution, reopen, history, attachments, feedback."""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..core.database import get_db
from ..core.deps import get_current_user, require_roles
from ..models import (
    Complaint, ComplaintHistory, Category, User, Role, Attachment, Feedback,
    PriorityEnum, StatusEnum,
)
from ..schemas.schemas import (
    ComplaintCreate, ComplaintUpdate, ComplaintOut, ComplaintListOut,
    ComplaintAssign, ComplaintStatusUpdate, ComplaintEscalate,
    ComplaintResolve, ComplaintReopen, HistoryOut, AttachmentOut,
    FeedbackCreate, FeedbackOut,
)
from ..services.complaint_service import (
    generate_complaint_number, compute_sla_due, log_history,
    create_notification, refresh_sla_breach, can_transition,
)


router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _scope_query_for_user(db: Session, user: User):
    """Customers see only their complaints; agents see assigned + unassigned; supervisors/admin see all."""
    q = db.query(Complaint).options(
        joinedload(Complaint.customer).joinedload(User.role),
        joinedload(Complaint.assigned_agent).joinedload(User.role),
        joinedload(Complaint.category),
        joinedload(Complaint.attachments),
        joinedload(Complaint.feedback),
    )
    role = user.role.name
    if role == "Customer":
        q = q.filter(Complaint.customer_id == user.id)
    elif role == "SupportAgent":
        q = q.filter(or_(Complaint.assigned_agent_id == user.id, Complaint.assigned_agent_id.is_(None)))
    # Supervisor / Admin → no scope filter
    return q


def _get_or_404(db: Session, complaint_id: int, user: User) -> Complaint:
    c = _scope_query_for_user(db, user).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(404, "Complaint not found or you don't have access")
    refresh_sla_breach(c)
    return c


def _list_projection(c: Complaint) -> ComplaintListOut:
    return ComplaintListOut(
        id=c.id,
        complaint_number=c.complaint_number,
        subject=c.subject,
        priority=c.priority,
        status=c.status,
        sla_due_at=c.sla_due_at,
        sla_breached=c.sla_breached,
        created_at=c.created_at,
        customer_name=c.customer.name,
        assigned_agent_name=c.assigned_agent.name if c.assigned_agent else None,
        category_name=c.category.name,
    )


# ---------------------------------------------------------------------------
# Create complaint  (Customer / Admin)
# ---------------------------------------------------------------------------
@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.role.name not in ("Customer", "Admin", "Supervisor"):
        raise HTTPException(403, "Only customers can register complaints")

    if not db.query(Category).filter(Category.id == payload.category_id, Category.is_active == True).first():  # noqa: E712
        raise HTTPException(400, "Invalid or inactive category")

    complaint = Complaint(
        complaint_number=generate_complaint_number(db),
        customer_id=current.id,
        category_id=payload.category_id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status=StatusEnum.OPEN,
        sla_due_at=compute_sla_due(payload.priority),
    )
    db.add(complaint)
    db.flush()       # ensure complaint.id is available for history

    log_history(db, complaint, current, "created", new_status=StatusEnum.OPEN,
                comment=f"Complaint registered with priority {payload.priority.value}")
    create_notification(db, current.id, "Complaint registered",
                        f"Your complaint {complaint.complaint_number} has been received.",
                        complaint.id)

    # Notify all supervisors so somebody can triage
    supervisors = db.query(User).join(Role).filter(Role.name == "Supervisor", User.is_active == True).all()  # noqa: E712
    for s in supervisors:
        create_notification(db, s.id, "New complaint awaiting triage",
                            f"{complaint.complaint_number} – {complaint.subject}",
                            complaint.id)

    db.commit()
    db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# List with search & filter
# ---------------------------------------------------------------------------
@router.get("", response_model=List[ComplaintListOut])
def list_complaints(
    q: Optional[str] = Query(default=None, description="Free-text search across subject/description/number"),
    status_filter: Optional[StatusEnum] = Query(default=None, alias="status"),
    priority: Optional[PriorityEnum] = None,
    category_id: Optional[int] = None,
    assigned_agent_id: Optional[int] = None,
    sla_breached: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    qry = _scope_query_for_user(db, current)

    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(
            Complaint.subject.ilike(like),
            Complaint.description.ilike(like),
            Complaint.complaint_number.ilike(like),
        ))
    if status_filter:
        qry = qry.filter(Complaint.status == status_filter)
    if priority:
        qry = qry.filter(Complaint.priority == priority)
    if category_id:
        qry = qry.filter(Complaint.category_id == category_id)
    if assigned_agent_id:
        qry = qry.filter(Complaint.assigned_agent_id == assigned_agent_id)
    if sla_breached is not None:
        qry = qry.filter(Complaint.sla_breached == sla_breached)
    if date_from:
        qry = qry.filter(Complaint.created_at >= date_from)
    if date_to:
        qry = qry.filter(Complaint.created_at <= date_to)

    rows = (
        qry.order_by(Complaint.created_at.desc())
           .offset((page - 1) * page_size)
           .limit(page_size)
           .all()
    )
    for c in rows:
        refresh_sla_breach(c)
    db.commit()  # persist any sla_breached flips
    return [_list_projection(c) for c in rows]


# ---------------------------------------------------------------------------
# Get / Update / Delete single complaint
# ---------------------------------------------------------------------------
@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return _get_or_404(db, complaint_id, current)


@router.put("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    # Customers can only edit their own complaints while still Open.
    if current.role.name == "Customer" and c.status != StatusEnum.OPEN:
        raise HTTPException(403, "Cannot edit a complaint that is already being processed")

    updates = payload.model_dump(exclude_unset=True)
    new_priority = updates.get("priority")
    if new_priority and new_priority != c.priority:
        c.sla_due_at = compute_sla_due(PriorityEnum(new_priority), base=c.created_at)
        log_history(db, c, current, "priority_change",
                    comment=f"Priority changed from {c.priority.value} to {new_priority.value}")
    for k, v in updates.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{complaint_id}", status_code=204)
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(404, "Complaint not found")
    db.delete(c)
    db.commit()


# ---------------------------------------------------------------------------
# Workflow actions
# ---------------------------------------------------------------------------
@router.post("/{complaint_id}/assign", response_model=ComplaintOut)
def assign_complaint(
    complaint_id: int,
    payload: ComplaintAssign,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("Admin", "Supervisor")),
):
    c = _get_or_404(db, complaint_id, current)
    agent = (
        db.query(User).join(Role)
        .filter(User.id == payload.agent_id, Role.name == "SupportAgent", User.is_active == True)  # noqa: E712
        .first()
    )
    if not agent:
        raise HTTPException(400, "Agent not found or not an active SupportAgent")

    old_agent = c.assigned_agent_id
    c.assigned_agent_id = agent.id
    if c.status in (StatusEnum.OPEN, StatusEnum.REOPENED):
        old_status = c.status
        c.status = StatusEnum.ASSIGNED
        log_history(db, c, current, "assigned", old_status=old_status, new_status=StatusEnum.ASSIGNED,
                    comment=f"Assigned to {agent.name}")
    else:
        log_history(db, c, current, "reassigned", comment=f"Reassigned to {agent.name}")

    create_notification(db, agent.id, "Complaint assigned to you",
                        f"{c.complaint_number}: {c.subject}", c.id)
    if old_agent and old_agent != agent.id:
        create_notification(db, old_agent, "Complaint reassigned",
                            f"{c.complaint_number} has been reassigned to {agent.name}", c.id)

    db.commit()
    db.refresh(c)
    return c


@router.post("/{complaint_id}/status", response_model=ComplaintOut)
def change_status(
    complaint_id: int,
    payload: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)

    role = current.role.name
    target = payload.status

    # Customers may only Close their own Resolved complaints (confirm resolution).
    if role == "Customer":
        if not (c.customer_id == current.id and c.status == StatusEnum.RESOLVED and target == StatusEnum.CLOSED):
            raise HTTPException(403, "Customers can only close their own resolved complaints")
    elif role == "SupportAgent" and c.assigned_agent_id != current.id:
        raise HTTPException(403, "You are not the agent assigned to this complaint")

    if not can_transition(c.status, target):
        raise HTTPException(400, f"Cannot transition from {c.status.value} to {target.value}")

    old = c.status
    c.status = target
    if target == StatusEnum.RESOLVED:
        c.resolved_at = datetime.utcnow()
    if target == StatusEnum.CLOSED:
        c.closed_at = datetime.utcnow()
    log_history(db, c, current, "status_change", old_status=old, new_status=target, comment=payload.comment)

    # Notify customer of status change
    create_notification(
        db, c.customer_id,
        f"Complaint {c.complaint_number} update",
        f"Status changed: {old.value} → {target.value}" + (f". Note: {payload.comment}" if payload.comment else ""),
        c.id,
    )
    db.commit()
    db.refresh(c)
    return c


@router.post("/{complaint_id}/escalate", response_model=ComplaintOut)
def escalate_complaint(
    complaint_id: int,
    payload: ComplaintEscalate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    if current.role.name == "Customer":
        raise HTTPException(403, "Customers cannot escalate; please add feedback instead")
    if not can_transition(c.status, StatusEnum.ESCALATED):
        raise HTTPException(400, f"Cannot escalate from status {c.status.value}")

    old = c.status
    c.status = StatusEnum.ESCALATED
    c.escalated_at = datetime.utcnow()
    c.escalation_reason = payload.reason
    log_history(db, c, current, "escalated", old_status=old, new_status=StatusEnum.ESCALATED, comment=payload.reason)

    # Alert all supervisors
    for s in db.query(User).join(Role).filter(Role.name == "Supervisor", User.is_active == True).all():  # noqa: E712
        create_notification(db, s.id, "Complaint escalated",
                            f"{c.complaint_number} escalated: {payload.reason[:120]}", c.id)
    db.commit()
    db.refresh(c)
    return c


@router.post("/{complaint_id}/resolve", response_model=ComplaintOut)
def resolve_complaint(
    complaint_id: int,
    payload: ComplaintResolve,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    if current.role.name == "Customer":
        raise HTTPException(403, "Only agents/supervisors/admin can mark a complaint resolved")
    if current.role.name == "SupportAgent" and c.assigned_agent_id != current.id:
        raise HTTPException(403, "Not your assigned complaint")
    if not can_transition(c.status, StatusEnum.RESOLVED):
        raise HTTPException(400, f"Cannot resolve from status {c.status.value}")

    old = c.status
    c.status = StatusEnum.RESOLVED
    c.resolution_notes = payload.resolution_notes
    c.resolved_at = datetime.utcnow()
    log_history(db, c, current, "resolved", old_status=old, new_status=StatusEnum.RESOLVED,
                comment=payload.resolution_notes)
    create_notification(
        db, c.customer_id,
        f"Complaint {c.complaint_number} resolved",
        "Please review the resolution and close the complaint or reopen if not satisfied.",
        c.id,
    )
    db.commit()
    db.refresh(c)
    return c


@router.post("/{complaint_id}/reopen", response_model=ComplaintOut)
def reopen_complaint(
    complaint_id: int,
    payload: ComplaintReopen,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    if current.role.name == "Customer" and c.customer_id != current.id:
        raise HTTPException(403, "Not your complaint")
    if not can_transition(c.status, StatusEnum.REOPENED):
        raise HTTPException(400, f"Cannot reopen from status {c.status.value}")

    old = c.status
    c.status = StatusEnum.REOPENED
    c.resolved_at = None
    c.closed_at = None
    # Reset SLA from now
    c.sla_due_at = compute_sla_due(c.priority)
    c.sla_breached = False
    log_history(db, c, current, "reopened", old_status=old, new_status=StatusEnum.REOPENED, comment=payload.reason)

    if c.assigned_agent_id:
        create_notification(db, c.assigned_agent_id, "Complaint reopened",
                            f"{c.complaint_number} has been reopened: {payload.reason[:120]}", c.id)
    db.commit()
    db.refresh(c)
    return c


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
@router.get("/{complaint_id}/history", response_model=List[HistoryOut])
def get_history(
    complaint_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    return (
        db.query(ComplaintHistory)
        .options(joinedload(ComplaintHistory.updated_by_user).joinedload(User.role))
        .filter(ComplaintHistory.complaint_id == c.id)
        .order_by(ComplaintHistory.updated_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------
@router.post("/{complaint_id}/attachments", response_model=AttachmentOut, status_code=201)
def upload_attachment(
    complaint_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    contents = file.file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(413, "File too large (max 10 MB)")

    ext = Path(file.filename).suffix
    stored = f"{c.complaint_number}_{uuid.uuid4().hex}{ext}"
    target = settings.UPLOAD_DIR / stored
    with open(target, "wb") as f:
        f.write(contents)

    att = Attachment(
        complaint_id=c.id,
        file_name=file.filename,
        stored_name=stored,
        content_type=file.content_type,
        size_bytes=len(contents),
        uploaded_by=current.id,
    )
    db.add(att)
    log_history(db, c, current, "attachment_uploaded", comment=f"Uploaded {file.filename}")
    db.commit()
    db.refresh(att)
    return att


@router.get("/{complaint_id}/attachments/{attachment_id}/download")
def download_attachment(
    complaint_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    att = db.query(Attachment).filter(
        Attachment.id == attachment_id, Attachment.complaint_id == c.id
    ).first()
    if not att:
        raise HTTPException(404, "Attachment not found")
    path = settings.UPLOAD_DIR / att.stored_name
    if not path.exists():
        raise HTTPException(410, "File no longer on disk")
    return FileResponse(path, filename=att.file_name, media_type=att.content_type or "application/octet-stream")


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
@router.post("/{complaint_id}/feedback", response_model=FeedbackOut, status_code=201)
def submit_feedback(
    complaint_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = _get_or_404(db, complaint_id, current)
    if c.customer_id != current.id and current.role.name != "Admin":
        raise HTTPException(403, "Only the complaint owner can submit feedback")
    if c.status not in (StatusEnum.RESOLVED, StatusEnum.CLOSED):
        raise HTTPException(400, "Feedback can only be submitted after resolution")
    if c.feedback:
        raise HTTPException(400, "Feedback already submitted")

    fb = Feedback(complaint_id=c.id, rating=payload.rating, comments=payload.comments)
    db.add(fb)
    log_history(db, c, current, "feedback_submitted",
                comment=f"Rating: {payload.rating}/5" + (f" – {payload.comments}" if payload.comments else ""))
    db.commit()
    db.refresh(fb)
    return fb
