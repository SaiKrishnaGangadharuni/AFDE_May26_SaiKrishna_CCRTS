"""ETL stage 3 — Load.

Persists cleaned & aggregated DataFrames into the analytics tables.
Each table is fully replaced (TRUNCATE + INSERT) so the dashboard always
reflects the latest ETL run.
"""
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.analytics_models import (
    AnalyticsComplaint,
    CategoryStat,
    SLABreachReport,
    ResolutionTrend,
    AgentPerformance,
)


def _to_python(v):
    """Convert Pandas NaT / NaN to None for SQLAlchemy."""
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, pd._libs.tslibs.nattype.NaTType):  # type: ignore[attr-defined]
        return None
    return v


def load_cleaned(db: Session, df: pd.DataFrame) -> int:
    """Replace analytics_complaints with the cleaned dataset."""
    db.query(AnalyticsComplaint).delete()
    rows = []
    for _, r in df.iterrows():
        rows.append(AnalyticsComplaint(
            complaint_id=str(r["complaint_id"]),
            complaint_category=_to_python(r["complaint_category"]) or "Unknown",
            priority=_to_python(r["priority"]) or "Medium",
            sla_hours=int(r["sla_hours"]) if not pd.isna(r["sla_hours"]) else 48,
            resolution_time_hours=_to_python(r["resolution_time_hours"]),
            status=_to_python(r["status"]) or "Open",
            agent_name=_to_python(r["agent_name"]),
            sla_breached=bool(r["sla_breached"]),
            created_date=_to_python(r["created_date"]),
            resolved_date=_to_python(r["resolved_date"]),
            loaded_at=datetime.utcnow(),
        ))
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def load_category_stats(db: Session, df: pd.DataFrame) -> int:
    db.query(CategoryStat).delete()
    rows = []
    for _, r in df.iterrows():
        rows.append(CategoryStat(
            category=str(r["category"]),
            total_complaints=int(r["total_complaints"]),
            resolved_count=int(r["resolved_count"]),
            breach_count=int(r["breach_count"]),
            avg_resolution_hours=_to_python(r["avg_resolution_hours"]),
            refreshed_at=datetime.utcnow(),
        ))
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def load_sla_breaches(db: Session, df: pd.DataFrame) -> int:
    db.query(SLABreachReport).delete()
    rows = []
    for _, r in df.iterrows():
        rows.append(SLABreachReport(
            priority=str(r["priority"]) if r["priority"] else "Unknown",
            total_complaints=int(r["total_complaints"]),
            breach_count=int(r["breach_count"]),
            breach_rate_pct=float(r["breach_rate_pct"]),
            refreshed_at=datetime.utcnow(),
        ))
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def load_resolution_trends(db: Session, df: pd.DataFrame) -> int:
    db.query(ResolutionTrend).delete()
    rows = []
    for _, r in df.iterrows():
        rows.append(ResolutionTrend(
            month=str(r["month"]),
            resolved_count=int(r["resolved_count"]),
            avg_resolution_hours=_to_python(r["avg_resolution_hours"]),
            breach_count=int(r["breach_count"]),
            refreshed_at=datetime.utcnow(),
        ))
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def load_agent_performance(db: Session, df: pd.DataFrame) -> int:
    db.query(AgentPerformance).delete()
    rows = []
    for _, r in df.iterrows():
        rows.append(AgentPerformance(
            agent_name=str(r["agent_name"]),
            handled_count=int(r["handled_count"]),
            resolved_count=int(r["resolved_count"]),
            breach_count=int(r["breach_count"]),
            avg_resolution_hours=_to_python(r["avg_resolution_hours"]),
            refreshed_at=datetime.utcnow(),
        ))
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)
