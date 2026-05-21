"""CCRTS Phase 2 — ETL package.

Three explicit stages:
  - extract.py    : read CSV/Excel dataset into a Pandas DataFrame
  - transform.py  : clean, normalize, compute SLA breach + derived fields
  - load.py       : persist cleaned data + aggregates into analytics tables

`run_etl.py` orchestrates Extract -> Transform -> Load.
"""
