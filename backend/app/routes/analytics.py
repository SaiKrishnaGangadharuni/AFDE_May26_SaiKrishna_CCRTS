"""Phase 2 — Analytics & ETL API endpoints.

Endpoints
---------
POST /api/etl/run                   Trigger the ETL pipeline (Admin/Supervisor)
GET  /api/etl/runs                  List recent ETL runs
GET  /api/etl/latest                Latest ETL run summary

GET  /api/analytics/summary         Overall summary numbers
GET  /api/analytics/sla-breaches    SLA breaches by priority
GET  /api/analytics/categories      Complaint counts by category
GET  /api/analytics/resolution-trends   Monthly resolution-time trends
GET  /api/analytics/agents          Agent performance

Authentication: all endpoints require a logged-in user.
ETL trigger is restricted to Admin / Supervisor roles per RBAC.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user, require_roles
from ..models import User
from ..models.analytics_models import (
    AnalyticsComplaint,
    CategoryStat,
    SLABreachReport,
    ResolutionTrend,
    AgentPerformance,
    ETLRunLog,
)
from ..schemas.analytics_schemas import (
    ETLRunSummary,
    SLABreachRow,
    CategoryStatRow,
    ResolutionTrendRow,
    AgentPerformanceRow,
    AnalyticsSummary,
)


router = APIRouter(tags=["Analytics & ETL"])


# ---------------------------------------------------------------------------
# ETL pipeline triggers
# ---------------------------------------------------------------------------
@router.post("/etl/run", response_model=ETLRunSummary, status_code=status.HTTP_201_CREATED)
def trigger_etl(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin", "Supervisor")),
):
    """Run the ETL pipeline against the default dataset.

    Returns the ETL run summary (rows extracted/cleaned/loaded + status).
    """
    # Import here to avoid a circular import at module load.
    from etl.run_etl import run_etl

    try:
        run_etl()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL failed: {e}",
        )

    latest = db.query(ETLRunLog).order_by(ETLRunLog.id.desc()).first()
    return latest


@router.get("/etl/runs", response_model=List[ETLRunSummary])
def list_etl_runs(
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.query(ETLRunLog).order_by(ETLRunLog.id.desc()).limit(limit).all()
    return rows


@router.get("/etl/latest", response_model=ETLRunSummary)
def latest_etl_run(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    latest = db.query(ETLRunLog).order_by(ETLRunLog.id.desc()).first()
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ETL run has been recorded yet.",
        )
    return latest


# ---------------------------------------------------------------------------
# Analytics reads
# ---------------------------------------------------------------------------
@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = db.query(func.count(AnalyticsComplaint.id)).scalar() or 0
    resolved = (
        db.query(func.count(AnalyticsComplaint.id))
        .filter(AnalyticsComplaint.status.in_(["Resolved", "Closed"]))
        .scalar() or 0
    )
    breaches = (
        db.query(func.count(AnalyticsComplaint.id))
        .filter(AnalyticsComplaint.sla_breached.is_(True))
        .scalar() or 0
    )
    avg_resolution = db.query(func.avg(AnalyticsComplaint.resolution_time_hours)).scalar()
    rate = round((breaches / total) * 100, 2) if total else 0.0
    last_run = db.query(ETLRunLog).order_by(ETLRunLog.id.desc()).first()

    return AnalyticsSummary(
        total_complaints=total,
        total_resolved=resolved,
        total_breaches=breaches,
        overall_breach_rate_pct=rate,
        avg_resolution_hours=round(avg_resolution, 2) if avg_resolution else None,
        last_run=last_run,
    )


@router.get("/analytics/sla-breaches", response_model=List[SLABreachRow])
def sla_breaches(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    rows = db.query(SLABreachReport).all()
    return sorted(rows, key=lambda r: order.get(r.priority, 99))


@router.get("/analytics/categories", response_model=List[CategoryStatRow])
def category_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(CategoryStat)
        .order_by(CategoryStat.total_complaints.desc())
        .all()
    )
    return rows


@router.get("/analytics/resolution-trends", response_model=List[ResolutionTrendRow])
def resolution_trends(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.query(ResolutionTrend).order_by(ResolutionTrend.month).all()
    return rows


@router.get("/analytics/agents", response_model=List[AgentPerformanceRow])
def agent_performance(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(AgentPerformance)
        .order_by(AgentPerformance.handled_count.desc())
        .all()
    )
    return rows
