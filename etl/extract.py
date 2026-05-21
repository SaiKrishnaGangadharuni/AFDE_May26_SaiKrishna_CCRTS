"""ETL stage 1 — Extract.

Reads the source dataset (CSV) into a Pandas DataFrame.
Per Phase 2 common instructions: input source is CSV/Excel using Pandas.
"""
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "complaint_id",
    "complaint_category",
    "priority",
    "sla_hours",
    "resolution_time_hours",
    "status",
    "agent_name",
    "created_date",
    "resolved_date",
]


def extract(source_path: str | Path) -> pd.DataFrame:
    """Load the dataset and verify the column schema."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Dataset not found: {source_path}")

    if source_path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(source_path)
    else:
        df = pd.read_csv(source_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    return df
