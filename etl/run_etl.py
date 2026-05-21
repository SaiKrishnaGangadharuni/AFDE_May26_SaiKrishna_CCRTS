"""ETL orchestrator — Extract -> Transform -> Load.

Can be run two ways:
  1. CLI:    python -m etl.run_etl
             python -m etl.run_etl --source datasets/complaints_dataset.csv
  2. Programmatically from the analytics API endpoint POST /api/etl/run
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path when this module is invoked
# from elsewhere (e.g. uvicorn -> routes/analytics.py).
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.database import SessionLocal, engine, Base   # noqa: E402
from backend.app.models.analytics_models import ETLRunLog          # noqa: E402

from etl.extract import extract              # noqa: E402
from etl.transform import (                  # noqa: E402
    transform,
    aggregate_category,
    aggregate_sla_breaches,
    aggregate_resolution_trends,
    aggregate_agent_performance,
)
from etl.load import (                       # noqa: E402
    load_cleaned,
    load_category_stats,
    load_sla_breaches,
    load_resolution_trends,
    load_agent_performance,
)


DEFAULT_DATASET = PROJECT_ROOT / "datasets" / "complaints_dataset.csv"


def run_etl(source_path: str | Path | None = None) -> dict:
    """Run the full ETL pipeline and return a summary dict."""
    src = Path(source_path) if source_path else DEFAULT_DATASET

    # Ensure analytics tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    log = ETLRunLog(
        started_at=datetime.utcnow(),
        source_file=str(src),
        status="running",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        # ---------- EXTRACT ----------
        df_raw = extract(src)
        log.rows_extracted = len(df_raw)

        # ---------- TRANSFORM ----------
        df_clean, stats = transform(df_raw)
        log.rows_after_clean = stats["rows_after_clean"]
        log.duplicates_dropped = stats["duplicates_dropped"]
        log.null_rows_dropped = stats["null_rows_dropped"]

        cat_df   = aggregate_category(df_clean)
        sla_df   = aggregate_sla_breaches(df_clean)
        trend_df = aggregate_resolution_trends(df_clean)
        agent_df = aggregate_agent_performance(df_clean)

        # ---------- LOAD ----------
        loaded = load_cleaned(db, df_clean)
        load_category_stats(db, cat_df)
        load_sla_breaches(db, sla_df)
        load_resolution_trends(db, trend_df)
        load_agent_performance(db, agent_df)

        log.rows_loaded = loaded
        log.status = "success"
        log.finished_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "run_id": log.id,
            "source_file": str(src),
            "rows_extracted": log.rows_extracted,
            "rows_after_clean": log.rows_after_clean,
            "duplicates_dropped": log.duplicates_dropped,
            "null_rows_dropped": log.null_rows_dropped,
            "rows_loaded": log.rows_loaded,
            "started_at": log.started_at.isoformat(),
            "finished_at": log.finished_at.isoformat(),
            "duration_seconds": (log.finished_at - log.started_at).total_seconds(),
        }
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)[:500]
        log.finished_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()


def _cli():
    parser = argparse.ArgumentParser(description="CCRTS Phase 2 ETL pipeline")
    parser.add_argument(
        "--source",
        default=str(DEFAULT_DATASET),
        help="Path to the source CSV/Excel dataset",
    )
    args = parser.parse_args()

    print(f"[ETL] Source: {args.source}")
    summary = run_etl(args.source)
    print("[ETL] Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    _cli()
