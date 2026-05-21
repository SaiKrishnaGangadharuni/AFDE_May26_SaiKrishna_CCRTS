"""Phase 2 — Analytics / Reporting tables.

These are SEPARATE from the operational tables in models.py.
Phase 2 spec: "Cleaned data should be stored in reporting/analytics tables."

The ETL pipeline (etl/) populates these tables from CSV datasets.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime

from ..core.database import Base


class AnalyticsComplaint(Base):
    """Cleaned complaint records produced by the ETL transform stage.

    One row per complaint after de-duplication and normalization.
    """
    __tablename__ = "analytics_complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(40), unique=True, nullable=False, index=True)
    complaint_category = Column(String(80), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    sla_hours = Column(Integer, nullable=False)
    resolution_time_hours = Column(Float, nullable=True)   # None if not yet resolved
    status = Column(String(40), nullable=False, index=True)
    agent_name = Column(String(80), nullable=True, index=True)
    sla_breached = Column(Boolean, nullable=False, default=False)
    created_date = Column(DateTime, nullable=True, index=True)
    resolved_date = Column(DateTime, nullable=True)
    loaded_at = Column(DateTime, default=datetime.utcnow)


class CategoryStat(Base):
    """Aggregate complaint counts per category."""
    __tablename__ = "analytics_category_stats"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(80), unique=True, nullable=False)
    total_complaints = Column(Integer, nullable=False, default=0)
    resolved_count = Column(Integer, nullable=False, default=0)
    breach_count = Column(Integer, nullable=False, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    refreshed_at = Column(DateTime, default=datetime.utcnow)


class SLABreachReport(Base):
    """Aggregate SLA breach counts grouped by priority."""
    __tablename__ = "analytics_sla_breaches"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(String(20), unique=True, nullable=False)
    total_complaints = Column(Integer, nullable=False, default=0)
    breach_count = Column(Integer, nullable=False, default=0)
    breach_rate_pct = Column(Float, nullable=False, default=0.0)
    refreshed_at = Column(DateTime, default=datetime.utcnow)


class ResolutionTrend(Base):
    """Monthly resolution-time trends — for line chart."""
    __tablename__ = "analytics_resolution_trends"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(7), unique=True, nullable=False)   # YYYY-MM
    resolved_count = Column(Integer, nullable=False, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    breach_count = Column(Integer, nullable=False, default=0)
    refreshed_at = Column(DateTime, default=datetime.utcnow)


class AgentPerformance(Base):
    """Agent-level performance metrics."""
    __tablename__ = "analytics_agent_performance"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(80), unique=True, nullable=False)
    handled_count = Column(Integer, nullable=False, default=0)
    resolved_count = Column(Integer, nullable=False, default=0)
    breach_count = Column(Integer, nullable=False, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    refreshed_at = Column(DateTime, default=datetime.utcnow)


class ETLRunLog(Base):
    """One row per ETL run — visible on the dashboard so user knows last refresh time."""
    __tablename__ = "analytics_etl_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    source_file = Column(String(255), nullable=False)
    rows_extracted = Column(Integer, default=0)
    rows_after_clean = Column(Integer, default=0)
    rows_loaded = Column(Integer, default=0)
    duplicates_dropped = Column(Integer, default=0)
    null_rows_dropped = Column(Integer, default=0)
    status = Column(String(20), default="running")   # running | success | failed
    error_message = Column(String(500), nullable=True)
