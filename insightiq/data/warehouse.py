"""Warehouse adapter with DuckDB preference and SQLite fallback."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

try:
    import duckdb
except Exception:
    duckdb = None


class Warehouse:
    """Query adapter — reads from SQLite/DuckDB, never from raw CSVs after first build.

    All pipeline data flows through this class after the warehouse is built.
    Production should use PostgreSQL or a cloud warehouse behind the same interface.
    """

    def __init__(self, sqlite_path: Path, duckdb_path: Path | None = None) -> None:
        self.sqlite_path = sqlite_path
        self.duckdb_path = duckdb_path

    def query(self, sql: str) -> pd.DataFrame:
        if self.duckdb_path and self.duckdb_path.exists() and duckdb is not None:
            with duckdb.connect(str(self.duckdb_path), read_only=True) as connection:
                return connection.execute(sql).df()
        with sqlite3.connect(self.sqlite_path) as connection:
            return pd.read_sql_query(sql, connection)

    def load_table(self, table: str) -> pd.DataFrame:
        """Load a full table from the warehouse into a DataFrame."""
        return self.query(f"SELECT * FROM {table}")

    def list_tables(self) -> list[str]:
        """Return all table names in the warehouse."""
        with sqlite3.connect(self.sqlite_path) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r[0] for r in rows]

    def export_duckdb_from_frames(self, frames: dict[str, pd.DataFrame]) -> Path | None:
        if duckdb is None or self.duckdb_path is None:
            return None
        if self.duckdb_path.exists():
            self.duckdb_path.unlink()
        with duckdb.connect(str(self.duckdb_path)) as connection:
            for name, frame in frames.items():
                connection.register("frame", frame)
                connection.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame")
                connection.unregister("frame")
        return self.duckdb_path

    def export_all_tables_to_csv(self, export_dir: Path) -> list[str]:
        """Export every table in the warehouse to CSV files in export_dir."""
        export_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for table in self.list_tables():
            df = self.load_table(table)
            out = export_dir / f"{table}.csv"
            df.to_csv(out, index=False)
            written.append(str(out))
        return written
