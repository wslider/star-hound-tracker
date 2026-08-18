"""
python/applications.py
----------------------
Application pipeline management for Star Hound Tracker (V1).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from python.db import get_connection
from python.jobs import get_job, list_jobs


STATUSES = [
    "saved",
    "applied",
    "interviewing",
    "offered",
    "accepted",
    "rejected_employer",
    "rejected_self",
    "withdrawn",
]


def generate_application_id() -> str:
    return uuid.uuid4().hex[:12]


def _has_active_application(job_id: str) -> bool:
    """Return True if there is already a non-archived application for this job."""
    sql = """
        SELECT 1 FROM applications
        WHERE job_id = ? AND archived = 0
        LIMIT 1
    """
    with get_connection() as conn:
        row = conn.execute(sql, (job_id,)).fetchone()
    return row is not None


def add_application(
    job_id: str,
    *,
    status: str = "saved",
    applied_date: str | None = None,
    next_follow_up: str | None = None,
    notes: str | None = None,
    archived: int = 0,
    allow_reapply: bool = False,
) -> str:
    """
    Create a new application linked to an existing job.

    By default prevents creating a second active application for the same job.
    Set allow_reapply=True if you really want to force it.
    """
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job {job_id} does not exist.")

    if not allow_reapply and _has_active_application(job_id):
        raise ValueError(
            f"An active application already exists for job {job_id}. "
            "Archive the old one first or pass allow_reapply=True."
        )

    application_id = generate_application_id()

    sql = """
        INSERT INTO applications (
            application_id, job_id, title, company, job_score,
            status, applied_date, next_follow_up, notes, archived
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        application_id,
        job_id,
        job.get("title"),
        job.get("company"),
        job.get("job_score"),
        status,
        applied_date,
        next_follow_up,
        notes,
        archived,
    )

    with get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()

    return application_id


def get_application(application_id: str) -> dict[str, Any] | None:
    sql = "SELECT * FROM applications WHERE application_id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (application_id,)).fetchone()
    return dict(row) if row else None


def list_applications(
    *,
    status: str | None = None,
    include_archived: bool = False,
    order_by_score: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    conditions = []
    params: list[Any] = []

    if not include_archived:
        conditions.append("archived = 0")

    if status:
        conditions.append("status = ?")
        params.append(status)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    order = "job_score DESC" if order_by_score else "applied_date DESC, application_id DESC"

    sql = f"""
        SELECT * FROM applications
        {where_clause}
        ORDER BY {order}
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [dict(row) for row in rows]


def update_application(application_id: str, **kwargs) -> bool:
    if not kwargs:
        return False

    allowed = {
        "status", "applied_date", "last_contact_date", "next_follow_up",
        "interview_stage", "offer_date", "offer_pay", "rejected_by",
        "notes", "archived", "title", "company", "job_score",
    }

    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    sql = f"UPDATE applications SET {set_clause} WHERE application_id = ?"
    values = list(updates.values()) + [application_id]

    with get_connection() as conn:
        cursor = conn.execute(sql, values)
        conn.commit()
        return cursor.rowcount > 0


def archive_application(application_id: str) -> bool:
    return update_application(application_id, archived=1)


# ----------------------------------------------------------------------
# Interactive helper
# ----------------------------------------------------------------------

def _ask(prompt: str, cast=None, allow_empty: bool = True):
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


def prompt_add_application(user_id: int = 1) -> str | None:
    """
    Interactive flow:
    1. Show top jobs that are not yet in the application pipeline
    2. Let user pick a job_id
    3. Create the application
    """
    print("\n=== Add Application ===\n")

    # Show jobs that don’t already have an active application
    existing_job_ids = {
        app["job_id"] for app in list_applications(include_archived=False)
    }

    available_jobs = [
        job for job in list_jobs(limit=30)
        if job["job_id"] not in existing_job_ids
    ]

    if not available_jobs:
        print("No available jobs to apply to (all jobs already have an active application).")
        return None

    print("Available jobs (not yet in pipeline):\n")
    for job in available_jobs:
        print(f"  {job['job_id']}  |  {job['job_score']:5.1f}  |  {job['title']} @ {job['company']}")

    print()
    job_id = _ask("Enter job_id to track: ", allow_empty=False)

    status = _ask("Starting status (default = saved): ") or "saved"
    notes = _ask("Notes: ")

    try:
        app_id = add_application(
            job_id=job_id,
            status=status,
            notes=notes,
        )
        print(f"\n✓ Application created!  ID: {app_id}")
        return app_id
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return None