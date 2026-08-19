"""
python/backup.py
----------------
Backup all SQLite tables to CSV files.
Structure: db_backups/YYYY-MM-DD/table_HHMMSS.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from python.db import get_connection

BACKUP_DIR = Path("db_backups")


def backup_all_tables() -> None:
    """
    Export every table to CSV files, organized by day.
    
    Example:
        db_backups/
          2026-08-19/
            user_105130.csv
            jobs_105130.csv
            applications_105130.csv
    """
    now = datetime.now()
    
    # Create day folder: db_backups/2026-08-19/
    day_folder = BACKUP_DIR / now.strftime("%Y-%m-%d")
    day_folder.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%H%M%S")  # just the time (HHMMSS)

    with get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        print(f"Backing up {len(tables)} table(s) → {day_folder}\n")

        for (table_name,) in tables:
            try:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

                filename = day_folder / f"{table_name}_{timestamp}.csv"
                df.to_csv(filename, index=False)

                print(f"✓ {table_name:20} → {filename.name}  ({len(df)} rows)")
            except Exception as e:
                print(f"✗ Failed to backup {table_name}: {e}")

    print(f"\nBackup complete → {day_folder}")


if __name__ == "__main__":
    backup_all_tables()