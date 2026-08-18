"""
python/reminders.py
-------------------
Follow-up reminders for Star Hound Tracker (V1).

Scans the applications table for items that need attention.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from python.db import get_connection
from python.applications import update_application, get_application


def get_due_followups(on_or_before: str | None = None) -> list[dict[str, Any]]:
    """
    Return applications that have a next_follow_up date
    on or before the given date (defaults to today).

    Only returns non-archived applications.
    """
    if on_or_before is None:
        on_or_before = date.today().isoformat()

    sql = """
        SELECT
            application_id,
            job_id,
            title,
            company,
            status,
            applied_date,
            last_contact_date,
            next_follow_up,
            interview_stage,
            notes,
            job_score
        FROM applications
        WHERE archived = 0
          AND next_follow_up IS NOT NULL
          AND next_follow_up <= ?
        ORDER BY next_follow_up ASC, job_score DESC
    """

    with get_connection() as conn:
        rows = conn.execute(sql, (on_or_before,)).fetchall()

    return [dict(row) for row in rows]


def get_upcoming_followups(days_ahead: int = 7) -> list[dict[str, Any]]:
    """
    Return applications with follow-ups due in the next X days
    (including today).
    """
    today = date.today()
    future = date.fromordinal(today.toordinal() + days_ahead).isoformat()

    sql = """
        SELECT
            application_id,
            job_id,
            title,
            company,
            status,
            applied_date,
            next_follow_up,
            notes,
            job_score
        FROM applications
        WHERE archived = 0
          AND next_follow_up IS NOT NULL
          AND next_follow_up >= ?
          AND next_follow_up <= ?
        ORDER BY next_follow_up ASC, job_score DESC
    """

    with get_connection() as conn:
        rows = conn.execute(sql, (today.isoformat(), future)).fetchall()

    return [dict(row) for row in rows]


def print_followup_report(days_ahead: int = 7) -> None:
    """
    Nice console report of due + upcoming follow-ups.
    """
    print("\n=== Follow-up Reminders ===\n")

    due = get_due_followups()
    upcoming = get_upcoming_followups(days_ahead=days_ahead)

    if not due and not upcoming:
        print("No follow-ups due or coming up. You're all caught up!")
        return

    if due:
        print("🔴 OVERDUE / DUE TODAY")
        print("-" * 60)
        for app in due:
            print(f"  {app['next_follow_up']}  |  {app['status']:12}  |  {app['title']} @ {app['company']}")
            if app.get("notes"):
                print(f"             Note: {app['notes']}")
        print()

    if upcoming:
        print(f"🟡 UPCOMING (next {days_ahead} days)")
        print("-" * 60)
        for app in upcoming:
            # Skip ones already shown in the "due" section
            if app in due:
                continue
            print(f"  {app['next_follow_up']}  |  {app['status']:12}  |  {app['title']} @ {app['company']}")
        print()

def complete_followup(
    application_id: str,
    *,
    next_follow_up: str | None = None,
    new_status: str | None = None,
    notes: str | None = None,
    interview_stage: int | None = None,
) -> bool:
    """
    Mark a follow-up as done.

    - Sets last_contact_date to today
    - Optionally sets a new next_follow_up date
    - Optionally updates status, notes, or interview_stage

    Returns True if the update succeeded.
    """
    today = date.today().isoformat()

    updates = {
        "last_contact_date": today,
    }

    # If the user supplies a new follow-up date, use it.
    # If they explicitly pass None, we clear it.
    if next_follow_up is not None:
        updates["next_follow_up"] = next_follow_up
    else:
        # Default behaviour: clear the follow-up so it disappears from the due list
        updates["next_follow_up"] = None

    if new_status is not None:
        updates["status"] = new_status

    if notes is not None:
        updates["notes"] = notes

    if interview_stage is not None:
        updates["interview_stage"] = interview_stage

    return update_application(application_id, **updates)

# helper function to mark follow up as complete

def prompt_complete_followup() -> None:
    """
    Interactive helper to mark a follow-up as done.
    """
    print("\n=== Complete Follow-up ===\n")

    due = get_due_followups()
    upcoming = get_upcoming_followups(days_ahead=14)

    all_relevant = due + [a for a in upcoming if a not in due]

    if not all_relevant:
        print("No follow-ups to complete.")
        return

    print("Select an application:\n")
    for i, app in enumerate(all_relevant, start=1):
        print(f"  {i}. {app['next_follow_up']}  |  {app['status']:12}  |  {app['title']} @ {app['company']}")

    print()
    choice = input("Enter number (or press Enter to cancel): ").strip()
    if not choice:
        print("Cancelled.")
        return

    try:
        idx = int(choice) - 1
        app = all_relevant[idx]
    except (ValueError, IndexError):
        print("Invalid choice.")
        return

    print(f"\nSelected: {app['title']} @ {app['company']}")

    new_follow = input("New next_follow_up date (YYYY-MM-DD) or leave blank to clear: ").strip()
    new_follow = new_follow if new_follow else None

    new_status = input(f"New status (current: {app['status']}) or leave blank: ").strip() or None
    notes = input("Add/update notes (or leave blank): ").strip() or None

    success = complete_followup(
        app["application_id"],
        next_follow_up=new_follow,
        new_status=new_status,
        notes=notes,
    )

    if success:
        print("✓ Follow-up updated.")
    else:
        print("✗ Something went wrong.")