"""
python/contacts.py
--------------
Networking management for Star Hound Tracker (V1).

Keep track of contacts and references.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from python.db import get_connection


def generate_contact_id() -> str:
    return uuid.uuid4().hex[:12]


def get_current_date() -> str:
    return date.today().isoformat()


def _has_contact(contact_id: str) -> bool:
    """Return True if a contact with this id already exists."""
    sql = """
        SELECT 1 FROM contacts
        WHERE contact_id = ?
        LIMIT 1
    """
    with get_connection() as conn:
        row = conn.execute(sql, (contact_id,)).fetchone()
    return row is not None


def add_contact(
    first_name: str | None = None,
    last_name: str | None = None,
    relationship: str | None = None,
    company: str | None = None,
    network_strength: int | None = None,
    last_contact_date: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    notes: str | None = None,
) -> str:
    contact_id = generate_contact_id()

    sql = """
        INSERT INTO contacts (
            contact_id,
            first_name,
            last_name,
            relationship,
            company,
            network_strength,
            last_contact_date,
            phone,
            email,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (
        contact_id,
        first_name,
        last_name,
        relationship,
        company,
        network_strength,
        last_contact_date,
        phone,
        email,
        notes,
    )

    with get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()

    return contact_id


def get_contact(contact_id: str) -> dict[str, Any] | None:
    sql = "SELECT * FROM contacts WHERE contact_id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (contact_id,)).fetchone()
    return dict(row) if row else None

def list_contacts() -> list[dict[str, Any]]:
    
    sql = f"""
        SELECT * FROM contacts
        ORDER BY network_strength DESC
        LIMIT 50;
    """

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    return [dict(row) for row in rows]


def update_contact(contact_id: str, **kwargs) -> bool:
    if not kwargs:
        return False

    allowed = {
        "first_name",
        "last_name",
        "relationship",
        "company",
        "network_strength",
        "last_contact_date",
        "phone",
        "email",
        "notes",
    }

    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    sql = f"UPDATE contacts SET {set_clause} WHERE contact_id = ?"
    values = list(updates.values()) + [contact_id]

    with get_connection() as conn:
        cursor = conn.execute(sql, values)
        conn.commit()
        return cursor.rowcount > 0


# Interactive Helpers


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


def prompt_add_contact() -> str | None:
    print("\n=== Add New Contact ===")
    print("(Press Enter to leave optional fields empty)\n")

    first_name = _ask("First Name: ", allow_empty=False)
    last_name = _ask("Last Name: ", allow_empty=False)
    relationship = _ask("Relationship: ", allow_empty=False)
    company = _ask("Company: ", allow_empty=False)
    network_strength = _ask("How Well Do You Know Each Other (1-10): ", cast=int)
    last_contact_date = _ask("Most Recent Communication: YYYY-MM-DD ")
    phone = _ask("Primary Phone Number: ")
    email = _ask("Email: ")
    notes = _ask("Notes: ")

    print("\nSaving contact...")

    contact_id = add_contact(
        first_name=first_name,
        last_name=last_name,
        relationship=relationship,
        company=company,
        network_strength=network_strength,
        last_contact_date=last_contact_date,
        phone=phone,
        email=email,
        notes=notes,
    )

    print(f"✓ contact added successfully!  ID: {contact_id}")
    return contact_id


def prompt_update_contact():
    pass