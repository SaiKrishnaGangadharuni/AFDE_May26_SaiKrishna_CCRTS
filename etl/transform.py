"""ETL stage 2 — Transform.

Per Phase 2 spec for CCRTS:
  - Transform priority and status fields
  - Compute SLA breach + resolution-time analytics

Cleaning rules applied (in order):
  1. Drop rows where all required fields are blank.
  2. Drop duplicates by complaint_id (keep first).
  3. Strip whitespace from every string column.
  4. Normalize 'priority' to {Low, Medium, High, Critical}.
  5. Normalize 'status' to canonical strings.
  6. Coerce numeric & datetime columns.
  7. Fill missing sla_hours from the canonical SLA table.
  8. Compute sla_breached = resolution_time_hours > sla_hours
     (NaN resolution -> still open -> not breached yet).
"""
import pandas as pd


# Canonical SLA per priority (must match the operational model: backend/app/models/models.py)
SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}


PRIORITY_NORMALIZATION = {
    "low": "Low", "lo": "Low",
    "medium": "Medium", "med": "Medium", "m": "Medium",
    "high": "High", "hi": "High",
    "critical": "Critical", "crit": "Critical", "c": "Critical",
}

STATUS_NORMALIZATION = {
    "open": "Open",
    "assigned": "Assigned",
    "in progress": "In Progress",
    "inprogress": "In Progress",
    "in_progress": "In Progress",
    "pending customer response": "Pending Customer Response",
    "escalated": "Escalated",
    "resolved": "Resolved",
    "closed": "Closed",
    "reopened": "Reopened",
}


def _norm_priority(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    key = str(val).strip().lower()
    return PRIORITY_NORMALIZATION.get(key, str(val).strip().title())


def _norm_status(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    key = str(val).strip().lower().replace("-", " ")
    return STATUS_NORMALIZATION.get(key, str(val).strip().title())


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean and normalize the raw extract.

    Returns: (cleaned_df, stats_dict)
        stats_dict carries counts used by the ETLRunLog.
    """
    stats = {
        "rows_extracted": len(df),
        "null_rows_dropped": 0,
        "duplicates_dropped": 0,
    }

    # 1. Drop fully-empty rows
    before = len(df)
    df = df.dropna(how="all").copy()
    # Also treat all-blank strings as empty
    blank_mask = df.apply(lambda r: all(
        (pd.isna(v) or str(v).strip() == "") for v in r), axis=1)
    df = df[~blank_mask]
    stats["null_rows_dropped"] = before - len(df)

    # 3. Strip whitespace on string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "": None})

    # 2. Drop duplicates by complaint_id (must come AFTER stripping)
    before = len(df)
    df = df.drop_duplicates(subset=["complaint_id"], keep="first")
    stats["duplicates_dropped"] = before - len(df)

    # 4. Normalize priority
    df["priority"] = df["priority"].apply(_norm_priority)

    # 5. Normalize status
    df["status"] = df["status"].apply(_norm_status)

    # 6. Numeric & datetime coercion
    df["sla_hours"] = pd.to_numeric(df["sla_hours"], errors="coerce")
    df["resolution_time_hours"] = pd.to_numeric(df["resolution_time_hours"], errors="coerce")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")

    # 7. Backfill SLA from canonical map if missing/wrong
    df["sla_hours"] = df.apply(
        lambda r: SLA_HOURS.get(r["priority"], r["sla_hours"])
        if pd.isna(r["sla_hours"]) else r["sla_hours"],
        axis=1
    ).astype("Int64")

    # 8. Compute SLA breach
    def _breach(row):
        rt = row["resolution_time_hours"]
        sla = row["sla_hours"]
        if pd.isna(rt) or pd.isna(sla):
            return False
        return bool(rt > sla)

    df["sla_breached"] = df.apply(_breach, axis=1)

    stats["rows_after_clean"] = len(df)
    return df.reset_index(drop=True), stats


# ---------- Aggregations (pure Pandas) ----------

def aggregate_category(df: pd.DataFrame) -> pd.DataFrame:
    """Per-category counts + averages."""
    g = df.groupby("complaint_category", dropna=False)
    out = g.agg(
        total_complaints=("complaint_id", "count"),
        resolved_count=("status", lambda s: (s.isin(["Resolved", "Closed"])).sum()),
        breach_count=("sla_breached", "sum"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
    ).reset_index().rename(columns={"complaint_category": "category"})
    out["breach_count"] = out["breach_count"].astype(int)
    out["resolved_count"] = out["resolved_count"].astype(int)
    return out


def aggregate_sla_breaches(df: pd.DataFrame) -> pd.DataFrame:
    """Per-priority breach rate."""
    g = df.groupby("priority", dropna=False)
    out = g.agg(
        total_complaints=("complaint_id", "count"),
        breach_count=("sla_breached", "sum"),
    ).reset_index()
    out["breach_count"] = out["breach_count"].astype(int)
    out["breach_rate_pct"] = (
        (out["breach_count"] / out["total_complaints"].replace(0, pd.NA)) * 100
    ).fillna(0).round(2)
    return out


def aggregate_resolution_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly resolution stats (uses resolved_date for resolved rows)."""
    resolved = df[df["resolved_date"].notna()].copy()
    if resolved.empty:
        return pd.DataFrame(columns=[
            "month", "resolved_count", "avg_resolution_hours", "breach_count"
        ])
    resolved["month"] = resolved["resolved_date"].dt.strftime("%Y-%m")
    g = resolved.groupby("month")
    out = g.agg(
        resolved_count=("complaint_id", "count"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        breach_count=("sla_breached", "sum"),
    ).reset_index().sort_values("month")
    out["breach_count"] = out["breach_count"].astype(int)
    return out


def aggregate_agent_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Per-agent performance metrics. Skips rows without an agent assigned."""
    agent_df = df[df["agent_name"].notna() & (df["agent_name"] != "")].copy()
    if agent_df.empty:
        return pd.DataFrame(columns=[
            "agent_name", "handled_count", "resolved_count",
            "breach_count", "avg_resolution_hours"
        ])
    g = agent_df.groupby("agent_name")
    out = g.agg(
        handled_count=("complaint_id", "count"),
        resolved_count=("status", lambda s: (s.isin(["Resolved", "Closed"])).sum()),
        breach_count=("sla_breached", "sum"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
    ).reset_index()
    out["breach_count"] = out["breach_count"].astype(int)
    out["resolved_count"] = out["resolved_count"].astype(int)
    return out
