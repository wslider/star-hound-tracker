"""
python/backup.py
----------------
Backup all SQLite tables to CSV files and one Excel workbook
(with each table as a sheet).

Real data:   db_backups/YYYY-MM-DD/
Sample data: samples/sample_backup_data/YYYY-MM-DD/
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from python.db import get_connection

DEFAULT_BACKUP_DIR = Path("db_backups")
SAMPLE_BACKUP_DIR = Path("samples/sample_backup_data")


def _autosize_columns(worksheet, df: pd.DataFrame, min_width: int = 12, max_width: int = 40) -> None:
    """Set column widths from header + cell length."""
    for idx, column in enumerate(df.columns, start=1):
        series = df[column].astype(str)
        longest = max([len(str(column))] + series.map(len).tolist()) if len(df) else len(str(column))
        width = min(max(longest + 2, min_width), max_width)
        worksheet.column_dimensions[worksheet.cell(1, idx).column_letter].width = width


def backup_all_tables(
    db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
) -> None:
    """Export every table to CSV + one Excel file, organized by day."""
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

                    csv_path = day_folder / f"{table_name}_{timestamp}.csv"
                    df.to_csv(csv_path, index=False)

                    sheet = table_name[:31]
                    df.to_excel(writer, sheet_name=sheet, index=False)

                    worksheet = writer.sheets[sheet]
                    _autosize_columns(worksheet, df)
                    worksheet.freeze_panes = "A2"
                    worksheet.auto_filter.ref = worksheet.dimensions

                    print(f"✓ {table_name:20} → {csv_path.name}  ({len(df)} rows)")
                except Exception as e:
                    print(f"✗ Failed to backup {table_name}: {e}")

    print(f"✓ Excel workbook → {excel_path.name}")
    print(f"\nBackup complete → {day_folder}")


def backup_real_tables() -> None:
    backup_all_tables()


def backup_sample_data() -> None:
    backup_all_tables(
        db_path=Path("samples/sample_jobs.db"),
        backup_dir=SAMPLE_BACKUP_DIR,
    )


if __name__ == "__main__":
    backup_real_tables()
    backup_sample_data()