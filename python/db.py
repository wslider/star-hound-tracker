import os
import sqlite3
from pathlib import Path

# Default path for real data
DB_PATH = Path("data") / "jobs.db"


def get_connection(db_path: Path | str | None = None):
    """
    Return a connection.
    If db_path is given, use it; otherwise use the default DB_PATH.
    """
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None):
    """
    Create folders + tables.
    Pass a custom db_path for sample/demo databases.
    """
    path = Path(db_path) if db_path is not None else DB_PATH

    # Create necessary folders
    for folder in ["data", "data/raw", "plots", "reports", "resumes", "samples"]:
        os.makedirs(folder, exist_ok=True)

    conn = get_connection(path)
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY,
            name TEXT, 
            city TEXT,
            state TEXT,
            lat REAL,
            lon REAL,
            preferred_pay_min REAL,
            preferred_pay_max REAL,
            max_weekly_commute_miles REAL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            level TEXT,
            employment_type TEXT,
            remote_policy TEXT,
            pay_usd_min REAL,
            pay_usd_max REAL,
            location_city TEXT,
            location_state TEXT,
            office_lat REAL,
            office_lon REAL,
            days_in_office_per_week REAL,
            one_way_commute_miles REAL,
            weekly_commute_miles REAL,
            skills TEXT,
            manual_match INTEGER,
            job_score REAL,
            score_pay REAL,
            score_commute REAL,
            score_match REAL,
            source_url TEXT,
            date_posted TEXT,
            date_added TEXT,
            raw_data_path TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            title TEXT,
            company TEXT,
            job_score REAL,
            status TEXT,
            applied_date TEXT,
            last_contact_date TEXT,
            next_follow_up TEXT,
            interview_stage INTEGER DEFAULT 0,
            offer_date TEXT,
            offer_pay REAL,
            rejected_by TEXT,
            notes TEXT,
            archived INTEGER DEFAULT 0,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        );
        """)
        conn.commit()
        print(f"Database ready: {path}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()