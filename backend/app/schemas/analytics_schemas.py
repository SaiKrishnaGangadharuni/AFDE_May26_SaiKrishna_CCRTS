"""Phase 2 — Pydantic response schemas for analytics endpoints."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class ETLRunSummary(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    source_file: str
    rows_extracted: int
    rows_after_clean: int
    rows_loaded: int
    duplicates_dropped: int
    null_rows_dropped: int
    status: str
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SLABreachRow(BaseModel):
    priority: str
    total_complaints: int
    breach_count: int
    breach_rate_pct: float
    model_config = ConfigDict(from_attributes=True)


class CategoryStatRow(BaseModel):
    category: str
    total_complaints: int
    resolved_count: int
    breach_count: int
    avg_resolution_hours: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class ResolutionTrendRow(BaseModel):
    month: str
    resolved_count: int
    avg_resolution_hours: Optional[float] = None
    breach_count: int
    model_config = ConfigDict(from_attributes=True)


class AgentPerformanceRow(BaseModel):
    agent_name: str
    handled_count: int
    resolved_count: int
    breach_count: int
    avg_resolution_hours: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummary(BaseModel):
    """Quick combined summary for the dashboard hero strip."""
    total_complaints: int
    total_resolved: int
    total_breaches: int
    overall_breach_rate_pct: float
    avg_resolution_hours: Optional[float] = None
    last_run: Optional[ETLRunSummary] = None
