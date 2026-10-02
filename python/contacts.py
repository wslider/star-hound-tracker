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

def prompt_list_contacts():
    contacts = list_contacts()
    print(contacts)

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
    print("\n=== Update Contact ===\n")
    
    contacts = list_contacts()

    if not contacts:
        print("No active applications found.")
        return False

    print("List of Contacts:\n")
    for i, contact in enumerate(contacts, start=1):
        print(f"  {i:2}. {contact['first_name']:18} | {contact['last_name']}  |  @ {contact['company']}")
        print(f"      Contact ID: {contact['contact_id']}")

    print()
    choice = input("Enter number (or full contact_id): ").strip()

    if not choice:
        print("Cancelled.")
        return False

    contact_id = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(contacts):
            contact_id = contacts[idx]["contact_id"]
        else:
            print("Invalid number.")
            return False
    else:
        contact_id = choice

    contact = get_contact(contact_id)
    if contact is None:
        print(f"Contact {contact_id} not found.")
        return False

    print(f"\nUpdating: {contact['first_name']} {contact['last_name']} @ {contact['company']}")
    print("(Press Enter to leave a field unchanged)\n")

    updates = {}

    company = input("Company: ").strip()
    if company:
        updates["company"] = company

    network_stength = input("Network Stength: ").strip()
    if network_stength:
        try:
            updates["network_stength"] = int(network_stength, range=(0,10))
        except ValueError:
            print("  → Invalid Value, enter a number between 1 and 10.")

    last_contact_date = input("Enter 'today' or Last Contact date (YYYY-MM-DD): ").strip()
    if last_contact_date.lower() == "today":
        last_contact_date = get_current_date()
    if last_contact_date:
        updates["last_contact_date"] = last_contact_date

    # validation of inputs later
    phone = input("Phone Number: ").strip()
    if phone:
        updates["phone"] = phone

    # validation of inputs later
    email = input("Email: ").strip()
    if email:
        updates["email"] = email

    # validation of inputs later
    notes = input("Notes: ").strip()
    if notes:
        updates["notes"] = notes

    if not updates:
        print("Nothing to update.")
        return False

    success = update_contact(contact_id, **updates)

    if success:
        print(f"\n✓ contact {contact_id} updated.")
    else:
        print("\n✗ Update failed.")

    return success