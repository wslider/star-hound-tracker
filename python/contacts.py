"""
python/contacts.py
--------------
Networking management for Star Hound Tracker (V1).

Keep track of contacts and refferences. 

"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from python.db import get_connection
from python.scoring import calculate_job_score
from python.users import get_user


def generate_contact_id() ->str:
    return uuid.uuid4().hex[:12] 

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
    user_id: int = 1,
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
            notes,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        user_id,
    )

    with get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()

    return contact_id



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



def prompt_add_contact(user_id: int = 1) -> str | None:
    
    print("\n=== Add New Contact ===")
    print("(Press Enter to leave optional fields empty)\n")

    first_name = _ask("First Name: ", allow_empty=False)
    last_name = _ask("Last Name: ", allow_empty=False)
    relationship = _ask("Relationship: ", allow_empty=False)
    company = _ask("Company: ", allow_empty=False)
    network_strength = _ask("How Well Do You Know Each Other (1-10): ", cast=int)
    last_contact_date = _ask("Most Revent Communication: YYYY-MM-DD ")
    phone = _ask("Primary Phone Number: ")
    email = _ask("Email: ")
    notes = _ask("Notes: ")

    print("\nSaving job...")

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
        user_id=user_id,
    )

    print(f"✓ contact added successfully!  ID: {contact_id}")
    return contact_id 