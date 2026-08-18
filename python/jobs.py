"""
python/jobs.py
--------------
Job management for Star Hound Tracker (V1).

Handles adding, retrieving, and listing jobs.
Uses the scoring module to calculate commute + job_score before saving.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from python.db import get_connection
from python.scoring import calculate_job_score
from python.users import get_user


def generate_job_id() -> str:
    """Generate a short unique job ID."""
    return uuid.uuid4().hex[:12]  # e.g. "a1b2c3d4e5f6"


def add_job(
    title: str,
    company: str,
    *,
    level: str | None = None,
    employment_type: str | None = None,
    remote_policy: str | None = None,
    pay_usd_min: float | None = None,
    pay_usd_max: float | None = None,
    location_city: str | None = None,
    location_state: str | None = None,
    office_lat: float | None = None,
    office_lon: float | None = None,
    days_in_office_per_week: float | None = None,
    one_way_commute_miles: float | None = None,
    skills: str | None = None,
    manual_match: int | None = None,
    source_url: str | None = None,
    date_posted: str | None = None,
    notes: str | None = None,
    user_id: int = 1,
) -> str:
    """
    Add a new job to the database.

    - Pulls the user profile for preferred pay / max commute
    - Calculates weekly_commute_miles + all score components
    - Inserts the full row into the jobs table

    Returns the new job_id.
    """
    # Get user preferences for scoring
    user = get_user(user_id) or {}

    # Calculate scores
    scores = calculate_job_score(
        pay_min=pay_usd_min,
        pay_max=pay_usd_max,
        one_way_commute_miles=one_way_commute_miles,
        days_in_office_per_week=days_in_office_per_week,
        remote_policy=remote_policy,
        manual_match=manual_match,
        preferred_pay_min=user.get("preferred_pay_min"),
        preferred_pay_max=user.get("preferred_pay_max"),
        max_weekly_commute_miles=user.get("max_weekly_commute_miles"),
    )

    job_id = generate_job_id()
    date_added = date.today().isoformat()

    sql = """
        INSERT INTO jobs (
            job_id, title, company, level, employment_type, remote_policy,
            pay_usd_min, pay_usd_max,
            location_city, location_state, office_lat, office_lon,
            days_in_office_per_week, one_way_commute_miles, weekly_commute_miles,
            skills, manual_match,
            job_score, score_pay, score_commute, score_match,
            source_url, date_posted, date_added, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        job_id,
        title,
        company,
        level,
        employment_type,
        remote_policy,
        pay_usd_min,
        pay_usd_max,
        location_city,
        location_state,
        office_lat,
        office_lon,
        days_in_office_per_week,
        one_way_commute_miles,
        scores["weekly_commute_miles"],
        skills,
        manual_match,
        scores["job_score"],
        scores["score_pay"],
        scores["score_commute"],
        scores["score_match"],
        source_url,
        date_posted,
        date_added,
        notes,
    )

    with get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()

    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    """Return a single job as a dictionary, or None if not found."""
    sql = "SELECT * FROM jobs WHERE job_id = ?"

    with get_connection() as conn:
        row = conn.execute(sql, (job_id,)).fetchone()

    return dict(row) if row else None


def list_jobs(
    limit: int = 50,
    order_by_score: bool = True,
) -> list[dict[str, Any]]:
    """
    Return a list of jobs.
    By default sorted by job_score descending (best first).
    """
    order = "job_score DESC" if order_by_score else "date_added DESC"

    sql = f"""
        SELECT * FROM jobs
        ORDER BY {order}
        LIMIT ?
    """

    with get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()

    return [dict(row) for row in rows]


def delete_job(job_id: str) -> bool:
    """
    Delete a job by ID.
    Returns True if a row was deleted.
    (Use carefully – in V1 we normally keep history.)
    """
    sql = "DELETE FROM jobs WHERE job_id = ?"

    with get_connection() as conn:
        cursor = conn.execute(sql, (job_id,))
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------------------------
# Interactive helper
# ----------------------------------------------------------------------

def _ask(prompt: str, cast=None, allow_empty: bool = True):
    """Small helper for interactive input."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and allow_empty:
            return None
        if cast is None:
            return raw
        try:
            return cast(raw)
        except ValueError:
            print("  → Invalid value, please try again.")


def prompt_add_job(user_id: int = 1) -> str | None:
    """
    Interactive version that asks for job details and calls add_job().
    Returns the new job_id, or None if the user cancels.
    """
    print("\n=== Add New Job ===")
    print("(Press Enter to leave optional fields empty)\n")

    title = _ask("Job title: ", allow_empty=False)
    company = _ask("Company: ", allow_empty=False)

    level = _ask("Level (junior/mid/senior/staff): ")
    employment_type = _ask("Employment type (full_time/part_time/contract/internship): ")
    remote_policy = _ask("Remote policy (onsite/hybrid/remote): ")

    pay_min = _ask("Pay min (USD annual): ", cast=float)
    pay_max = _ask("Pay max (USD annual): ", cast=float)

    location_city = _ask("Location city: ")
    location_state = _ask("Location state: ")

    days = _ask("Days in office per week (0 for remote): ", cast=float)
    one_way = _ask("One-way commute miles (0 if remote): ", cast=float)

    manual_match = _ask("Manual match (1-10): ", cast=int)
    skills = _ask("Skills (comma-separated): ")
    source_url = _ask("Source URL: ")
    notes = _ask("Notes: ")

    print("\nSaving job...")

    job_id = add_job(
        title=title,
        company=company,
        level=level,
        employment_type=employment_type,
        remote_policy=remote_policy,
        pay_usd_min=pay_min,
        pay_usd_max=pay_max,
        location_city=location_city,
        location_state=location_state,
        days_in_office_per_week=days,
        one_way_commute_miles=one_way,
        manual_match=manual_match,
        skills=skills,
        source_url=source_url,
        notes=notes,
        user_id=user_id,
    )

    print(f"✓ Job added successfully!  ID: {job_id}")
    return job_id