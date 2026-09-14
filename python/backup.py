"""
python/backup.py
----------------
Backup all SQLite tables to CSV files.
Backup to Excel file with tables as sheets. 

Default (real data):
    db_backups/YYYY-MM-DD/table_HHMMSS.csv

Sample data:
    samples/sample_backup_data/YYYY-MM-DD/table_HHMMSS.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from python.db import get_connection

# Default locations
DEFAULT_BACKUP_DIR = Path("db_backups")
SAMPLE_BACKUP_DIR = Path("samples/sample_backup_data")


def backup_all_tables(
    db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
) -> None:
    """
    Export every table to CSV files, organized by day.

    Parameters
    ----------
    db_path : optional
        Path to the SQLite database. Defaults to the real data/jobs.db.
    backup_dir : optional
        Folder where the dated subfolders will be created.
        Defaults to db_backups/ for real data.
    """
    # Resolve paths
    backup_root = Path(backup_dir) if backup_dir is not None else DEFAULT_BACKUP_DIR

    now = datetime.now()
    day_folder = backup_root / now.strftime("%Y-%m-%d")
    day_folder.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%H%M%S")

    excel_path = day_folder / f"job_data_{timestamp}.xlsx"

    with get_connection(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()

        if not tables:
            print("No tables found in the database.")
            return
        print(f"Backing up {len(tables)} table(s) → {day_folder}\n")

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for (table_name,) in tables:
                try:
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

                    # CSV (keep what you already have)
                    csv_path = day_folder / f"{table_name}_{timestamp}.csv"
                    df.to_csv(csv_path, index=False)

                    # Excel sheet names max out at 31 characters
                    sheet = table_name[:31]
                    df.to_excel(writer, sheet_name=sheet, index=False)

                    print(f"✓ {table_name:20} → {csv_path.name}  ({len(df)} rows)")
                    

                except Exception as e:
                    print(f"✗ Failed to backup {table_name}: {e}")

    print(f"✓ Excel workbook → {excel_path.name}")
    print(f"\nBackup complete → {day_folder}")





def backup_sample_data() -> None:
    """Convenience helper: backup the sample database."""
    sample_db = Path("samples/sample_jobs.db")
    backup_all_tables(
        db_path=sample_db,
        backup_dir=SAMPLE_BACKUP_DIR,
    )


if __name__ == "__main__":
    # Default = real data
    backup_all_tables()

    # Uncomment if you also want to backup sample data when run directly
    backup_sample_data()