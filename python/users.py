"""
python/users.py
---------------
User profile management for Star Hound Tracker (V1).

V1 assumes a single primary user (user_id = 1),
but the functions already support multiple users for future flexibility.
"""

from __future__ import annotations
from typing import Any
from python.db import get_connection


# Database functions (no input() here – easy to test)


def create_user(
    name: str | None = None,
    city: str | None = None,
    state: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    preferred_pay_min: float | None = None,
    preferred_pay_max: float | None = None,
    max_weekly_commute_miles: float | None = None,
    notes: str | None = None,
    user_id: int = 1,
) -> int:
    """
    Create a user, or replace the existing one if the user_id already exists.
    
    Uses INSERT OR REPLACE so it never raises a UNIQUE constraint error.
    Returns the user_id.
    """
    sql = """
        INSERT OR REPLACE INTO user (
            user_id, name, city, state, lat, lon,
            preferred_pay_min, preferred_pay_max,
            max_weekly_commute_miles, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (
        user_id,
        name,
        city,
        state,
        lat,
        lon,
        preferred_pay_min,
        preferred_pay_max,
        max_weekly_commute_miles,
        notes,
    )

    with get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()

    return user_id

def get_user(user_id: int = 1) -> dict[str, Any] | None:
    """
    Fetch a single user by user_id.
    Returns a dictionary or None if the user does not exist.
    """
    sql = "SELECT * FROM user WHERE user_id = ?"

    with get_connection() as conn:
        row = conn.execute(sql, (user_id,)).fetchone()

    if row is None:
        return None

    # Convert sqlite3.Row → normal dict (easier to work with)
    return dict(row)


def list_users() -> list[dict[str, Any]]:
    """
    Return all users as a list of dictionaries.
    Useful for debugging and for V2 multi-user support.
    """
    sql = "SELECT * FROM user ORDER BY user_id"

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    return [dict(row) for row in rows]


def update_user(user_id: int = 1, **kwargs) -> bool:
    """
    Update only the fields that are provided.

    Example:
        update_user(1, city="Austin", preferred_pay_min=120000)

    Returns True if a row was updated, False if the user_id was not found.
    """
    if not kwargs:
        return False  # nothing to update

    # Build the SET clause dynamically
    allowed_columns = {
        "name", "city", "state", "lat", "lon",
        "preferred_pay_min", "preferred_pay_max",
        "max_weekly_commute_miles", "notes",
    }

    # Filter out any unexpected keys
    updates = {k: v for k, v in kwargs.items() if k in allowed_columns}

    if not updates:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in updates.keys())
    sql = f"UPDATE user SET {set_clause} WHERE user_id = ?"

    values = list(updates.values()) + [user_id]

    with get_connection() as conn:
        cursor = conn.execute(sql, values)
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------------------------
# Interactive helpers (these use input() – call them from the CLI/menu)
# ----------------------------------------------------------------------

def _ask(prompt: str, cast=None, allow_empty: bool = True):
    """
    Small helper to ask a question and optionally convert the answer.
    Returns None if the user just presses Enter (and allow_empty=True).
    """
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


def prompt_create_user(user_id: int = 1) -> int:
    """
    Interactive version that asks the user for profile information
    and then calls create_user().
    """
    print("\n=== Create User Profile ===")
    print("(Press Enter to leave a field empty)\n")

    name = _ask("Name: ")
    city = _ask("Home city: ")
    state = _ask("Home state (e.g. TX): ")
    lat = _ask("Home latitude: ", cast=float)
    lon = _ask("Home longitude: ", cast=float)
    preferred_pay_min = _ask("Preferred minimum pay (annual USD): ", cast=float)
    preferred_pay_max = _ask("Preferred maximum pay (annual USD): ", cast=float)
    max_weekly_commute = _ask("Max weekly commute miles (soft limit): ", cast=float)
    notes = _ask("Notes: ")

    user_id = create_user(
        name=name,
        city=city,
        state=state,
        lat=lat,
        lon=lon,
        preferred_pay_min=preferred_pay_min,
        preferred_pay_max=preferred_pay_max,
        max_weekly_commute_miles=max_weekly_commute,
        notes=notes,
        user_id=user_id,
    )

    print(f"\n✓ User {user_id} created successfully.")
    return user_id


def prompt_update_user(user_id: int = 1) -> bool:
    """
    Simple interactive update – only updates fields the user actually fills in.
    """
    print(f"\n=== Update User {user_id} ===")
    print("(Press Enter to skip a field)\n")

    updates = {}

    name = _ask("New name: ")
    if name is not None:
        updates["name"] = name

    city = _ask("New city: ")
    if city is not None:
        updates["city"] = city

    state = _ask("New state: ")
    if state is not None:
        updates["state"] = state

    lat = _ask("New latitude: ", cast=float)
    if lat is not None:
        updates["lat"] = lat

    lon = _ask("New longitude: ", cast=float)
    if lon is not None:
        updates["lon"] = lon

    pay_min = _ask("New preferred pay min: ", cast=float)
    if pay_min is not None:
        updates["preferred_pay_min"] = pay_min

    pay_max = _ask("New preferred pay max: ", cast=float)
    if pay_max is not None:
        updates["preferred_pay_max"] = pay_max

    commute = _ask("New max weekly commute miles: ", cast=float)
    if commute is not None:
        updates["max_weekly_commute_miles"] = commute

    notes = _ask("New notes: ")
    if notes is not None:
        updates["notes"] = notes

    if not updates:
        print("Nothing to update.")
        return False

    success = update_user(user_id, **updates)
    if success:
        print("✓ User updated.")
    else:
        print("✗ User not found or nothing changed.")
    return success