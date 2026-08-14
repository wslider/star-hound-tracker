import os
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "jobs.db"

def get_connection():
    # Make sure parent folder exists before connecting
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    conn.row_factory = sqlite3.Row          # allows dict-like access
    return conn

def init_db():
    # Create necessary folders
    for path in ["data", "data/raw", "plots", "reports", "resumes"]:
        os.makedirs(path, exist_ok=True)

    conn = get_connection()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY,
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
        print(f"Database ready: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()