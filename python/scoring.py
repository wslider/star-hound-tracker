"""
python/scoring.py
-----------------
Pure scoring logic for Star Hound Tracker (V1).

No database access here – just calculations.
Used by the jobs module when adding or updating a job.
"""

from __future__ import annotations
from typing import Any


def calculate_weekly_commute(
    one_way_commute_miles: float | None,
    days_in_office_per_week: float | None,
    remote_policy: str | None = None,
) -> float:
    """
    Calculate weekly commute miles.

    Rules:
    - remote  → 0
    - otherwise → one_way * 2 * days_in_office
    """
    if remote_policy and remote_policy.lower() == "remote":
        return 0.0

    one_way = one_way_commute_miles or 0.0
    days = days_in_office_per_week or 0.0

    return round(one_way * 2 * days, 1)


def normalize_pay(
    pay_min: float | None,
    pay_max: float | None,
    preferred_min: float | None,
    preferred_max: float | None,
) -> float:
    """
    Return a pay score between 0.0 and 1.0.

    Simple but useful V1 logic:
    - Uses the midpoint of the offered range
    - Scores higher when the offer is inside or above the preferred range
    """
    if pay_min is None and pay_max is None:
        return 0.5  # neutral if unknown

    # Use midpoint of the offered range
    if pay_min is not None and pay_max is not None:
        offer = (pay_min + pay_max) / 2
    elif pay_min is not None:
        offer = pay_min
    else:
        offer = pay_max

    pref_min = preferred_min or 0
    pref_max = preferred_max or (pref_min * 1.5 if pref_min else 150000)

    if offer >= pref_max:
        return 1.0
    if offer <= pref_min:
        # Linear falloff below the minimum
        if pref_min == 0:
            return 0.0
        return max(0.0, offer / pref_min * 0.6)

    # Inside the preferred range → scale from 0.7 to 1.0
    range_size = pref_max - pref_min
    if range_size <= 0:
        return 0.85
    position = (offer - pref_min) / range_size
    return 0.7 + (position * 0.3)


def normalize_commute(
    weekly_commute_miles: float,
    max_preferred_miles: float | None = None,
) -> float:
    """
    Return a commute score between 0.0 and 1.0.
    Lower miles = higher score.
    """
    if weekly_commute_miles <= 0:
        return 1.0  # remote or no commute

    max_miles = max_preferred_miles or 150  # soft default

    if weekly_commute_miles >= max_miles * 1.5:
        return 0.0

    # Linear score from 1.0 (0 miles) down to 0.0
    score = 1.0 - (weekly_commute_miles / (max_miles * 1.5))
    return max(0.0, min(1.0, score))


def normalize_match(manual_match: int | None) -> float:
    """Convert 1–10 manual match into 0.0–1.0"""
    if manual_match is None:
        return 0.5
    return max(0.0, min(1.0, manual_match / 10.0))


def calculate_job_score(
    *,
    pay_min: float | None = None,
    pay_max: float | None = None,
    one_way_commute_miles: float | None = None,
    days_in_office_per_week: float | None = None,
    remote_policy: str | None = None,
    manual_match: int | None = None,
    preferred_pay_min: float | None = None,
    preferred_pay_max: float | None = None,
    max_weekly_commute_miles: float | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Main scoring function.

    Returns a dictionary with:
        - weekly_commute_miles
        - score_pay
        - score_commute
        - score_match
        - job_score          (0–100)
    """
    # Default weights (easy to tune later)
    if weights is None:
        weights = {
            "pay": 0.40,
            "commute": 0.25,
            "match": 0.35,
        }

    weekly = calculate_weekly_commute(
        one_way_commute_miles,
        days_in_office_per_week,
        remote_policy,
    )

    score_pay = normalize_pay(pay_min, pay_max, preferred_pay_min, preferred_pay_max)
    score_commute = normalize_commute(weekly, max_weekly_commute_miles)
    score_match = normalize_match(manual_match)

    job_score = 100 * (
        weights["pay"] * score_pay
        + weights["commute"] * score_commute
        + weights["match"] * score_match
    )

    return {
        "weekly_commute_miles": weekly,
        "score_pay": round(score_pay, 3),
        "score_commute": round(score_commute, 3),
        "score_match": round(score_match, 3),
        "job_score": round(job_score, 1),
    }


# ----------------------------------------------------------------------
# Quick manual test (only runs when you execute this file directly)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Scoring module test ===\n")

    # Example 1: Hybrid job
    result1 = calculate_job_score(
        pay_min=125000,
        pay_max=145000,
        one_way_commute_miles=18,
        days_in_office_per_week=3,
        remote_policy="hybrid",
        manual_match=8,
        preferred_pay_min=120000,
        preferred_pay_max=160000,
        max_weekly_commute_miles=100,
    )
    print("Hybrid job:", result1)

    # Example 2: Fully remote
    result2 = calculate_job_score(
        pay_min=130000,
        pay_max=150000,
        remote_policy="remote",
        manual_match=9,
        preferred_pay_min=120000,
        preferred_pay_max=160000,
    )
    print("Remote job:", result2)

    # Example 3: Low pay + long commute
    result3 = calculate_job_score(
        pay_min=85000,
        pay_max=95000,
        one_way_commute_miles=35,
        days_in_office_per_week=5,
        remote_policy="onsite",
        manual_match=6,
        preferred_pay_min=120000,
        preferred_pay_max=160000,
        max_weekly_commute_miles=100,
    )
    print("Low-pay onsite:", result3)