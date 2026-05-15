"""Dashboard & analytics — stats, agent performance, category breakdown, trends."""
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Complaint, Category, User, Role, StatusEnum, Feedback
from ..schemas.schemas import (
    DashboardStats, AgentPerformance, CategoryStats, TrendPoint,
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


def _avg_resolution_hours(db: Session, base_query):
    """Average hours between created_at and resolved_at across a query of Complaints."""
    rows = base_query.filter(Complaint.resolved_at.isnot(None)).with_entities(
        Complaint.created_at, Complaint.resolved_at
    ).all()
    if not rows:
        return None
    total = sum((r.resolved_at - r.created_at).total_seconds() for r in rows)
    return round((total / len(rows)) / 3600.0, 2)


@router.get("/stats", response_model=DashboardStats)
def overall_stats(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Stats scoped by role:
      Customer → their own complaints
      SupportAgent → complaints assigned to them
      Supervisor / Admin → all
    """
    q = db.query(Complaint)
    role = current.role.name
    if role == "Customer":
        q = q.filter(Complaint.customer_id == current.id)
    elif role == "SupportAgent":
        q = q.filter(Complaint.assigned_agent_id == current.id)

    def count_status(s: StatusEnum) -> int:
        return q.filter(Complaint.status == s).count()

    return DashboardStats(
        total_complaints=q.count(),
        open=count_status(StatusEnum.OPEN),
        in_progress=count_status(StatusEnum.IN_PROGRESS),
        pending_customer=count_status(StatusEnum.PENDING_CUSTOMER),
        escalated=count_status(StatusEnum.ESCALATED),
        resolved=count_status(StatusEnum.RESOLVED),
        closed=count_status(StatusEnum.CLOSED),
        reopened=count_status(StatusEnum.REOPENED),
        sla_breaches=q.filter(Complaint.sla_breached == True).count(),  # noqa: E712
        avg_resolution_hours=_avg_resolution_hours(db, q),
    )


@router.get("/agent-performance", response_model=List[AgentPerformance])
def agent_performance(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin", "Supervisor")),
):
    agents = db.query(User).join(Role).filter(Role.name == "SupportAgent").all()
    output: List[AgentPerformance] = []
    for a in agents:
        q = db.query(Complaint).filter(Complaint.assigned_agent_id == a.id)
        total = q.count()
        resolved = q.filter(Complaint.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED])).count()
        breaches = q.filter(Complaint.sla_breached == True).count()  # noqa: E712
        output.append(AgentPerformance(
            agent_id=a.id,
            agent_name=a.name,
            total_assigned=total,
            resolved=resolved,
            avg_resolution_hours=_avg_resolution_hours(db, q),
            sla_breaches=breaches,
        ))
    return sorted(output, key=lambda x: x.total_assigned, reverse=True)


@router.get("/category-breakdown", response_model=List[CategoryStats])
def category_breakdown(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(Category.id, Category.name, func.count(Complaint.id))
        .outerjoin(Complaint, Complaint.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    return [CategoryStats(category_id=r[0], category_name=r[1], total=r[2]) for r in rows]


@router.get("/trends", response_model=List[TrendPoint])
def trends(
    months: int = 6,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Per-month complaint volume + resolved count for the last `months` months."""
    cutoff = datetime.utcnow().replace(day=1) - timedelta(days=months * 31)
    rows = (
        db.query(
            func.strftime("%Y-%m", Complaint.created_at).label("period"),
            func.count(Complaint.id).label("total"),
            func.sum(case((Complaint.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED]), 1), else_=0)).label("resolved"),
        )
        .filter(Complaint.created_at >= cutoff)
        .group_by("period")
        .order_by("period")
        .all()
    )
    return [TrendPoint(period=r[0], total=r[1] or 0, resolved=int(r[2] or 0)) for r in rows]


@router.get("/customer-satisfaction")
def customer_satisfaction(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin", "Supervisor")),
):
    rows = db.query(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating).all()
    distribution = {str(r[0]): r[1] for r in rows}
    avg = db.query(func.avg(Feedback.rating)).scalar()
    return {
        "average_rating": round(float(avg), 2) if avg is not None else None,
        "total_responses": sum(distribution.values()),
        "distribution": distribution,
    }
