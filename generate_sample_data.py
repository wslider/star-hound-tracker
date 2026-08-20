"""
generate_sample_data.py
-----------------------
Creates a completely separate sample database + realistic demo data
for Star Hound Tracker.

- Does NOT touch data/jobs.db
- Uses all existing python/ modules
- Ready for viz.py later (just add calls at the bottom)
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

# -------------------------------------------------
# Point everything at the SAMPLE database
# -------------------------------------------------
SAMPLE_DB = Path("samples/sample_jobs.db")
SAMPLE_DB.parent.mkdir(parents=True, exist_ok=True)

# Temporary monkey-patch so existing modules use the sample DB
import python.db as db
db.DB_PATH = SAMPLE_DB

from python.db import init_db, get_connection
from python.users import create_user
from python.jobs import add_job
from python.applications import add_application, update_application
from python.scoring import calculate_job_score   # already used internally by add_job


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def generate():
    print("=== Generating sample data for Star Hound Tracker ===\n")

    # 1. Fresh sample database
    if SAMPLE_DB.exists():
        SAMPLE_DB.unlink()
    init_db()
    print(f"✓ Sample database created → {SAMPLE_DB}")

    # 2. Create the fun sample user
    create_user(
        name="Star Hound",
        city="Frozen Beaver Falls",
        state="KY",
        lat=36.91,
        lon=-82.91,
        preferred_pay_min=110_000,
        preferred_pay_max=160_000,
        max_weekly_commute_miles=100,
        notes="Sample profile – Data Analyst seeking remote or hybrid roles in food-tech / analytics.",
    )
    print("✓ User 'Star Hound' created")

    # 3. Sample jobs (playful but realistic)
    sample_jobs = [
        # High-score remote / hybrid
        dict(title="Senior Data Analyst", company="BeaverBite Analytics", level="senior",
             employment_type="full_time", remote_policy="remote",
             pay_usd_min=135000, pay_usd_max=155000, location_city="Remote", location_state="",
             days_in_office_per_week=0, one_way_commute_miles=0, manual_match=9,
             skills="Python, SQL, Tableau, pandas, A/B testing"),
        
        dict(title="Food Data Scientist", company="Frosty Fork Labs", level="mid",
             employment_type="full_time", remote_policy="hybrid",
             pay_usd_min=125000, pay_usd_max=145000, location_city="Louisville", location_state="KY",
             days_in_office_per_week=2, one_way_commute_miles=45, manual_match=8,
             skills="Python, scikit-learn, SQL, food science domain"),

        dict(title="Analytics Engineer", company="Maple & Metric", level="senior",
             employment_type="full_time", remote_policy="remote",
             pay_usd_min=140000, pay_usd_max=165000, location_city="Remote", location_state="",
             days_in_office_per_week=0, one_way_commute_miles=0, manual_match=9,
             skills="dbt, Snowflake, Python, Looker"),

        # Medium scores
        dict(title="Business Intelligence Analyst", company="Creekside Consumer Co", level="mid",
             employment_type="full_time", remote_policy="hybrid",
             pay_usd_min=105000, pay_usd_max=125000, location_city="Lexington", location_state="KY",
             days_in_office_per_week=3, one_way_commute_miles=55, manual_match=7,
             skills="SQL, Power BI, Excel, Python"),

        dict(title="Junior Data Analyst", company="Pawprint Pet Foods", level="junior",
             employment_type="full_time", remote_policy="remote",
             pay_usd_min=85000, pay_usd_max=100000, location_city="Remote", location_state="",
             days_in_office_per_week=0, one_way_commute_miles=0, manual_match=6,
             skills="SQL, Tableau, Excel"),

        # Lower / longer commute
        dict(title="Data Analyst", company="Bluegrass Brewing Data", level="mid",
             employment_type="full_time", remote_policy="onsite",
             pay_usd_min=95000, pay_usd_max=115000, location_city="Frankfort", location_state="KY",
             days_in_office_per_week=5, one_way_commute_miles=70, manual_match=5,
             skills="SQL, Python, Excel"),

        dict(title="Marketing Data Analyst", company="Frozen Falls Marketing", level="mid",
             employment_type="full_time", remote_policy="hybrid",
             pay_usd_min=100000, pay_usd_max=120000, location_city="Hazard", location_state="KY",
             days_in_office_per_week=2, one_way_commute_miles=90, manual_match=6,
             skills="Google Analytics, SQL, Python"),
    ]

    # Add a few more random variations so charts look alive
    companies = ["Riverbend Analytics", "Summit Snack Co", "Cloudberry Insights",
                 "Oak & Open Data", "Lumen Food Tech", "Cascade Metrics"]
    titles = ["Data Analyst", "Senior Analyst", "Analytics Specialist", "BI Developer"]
    
    for i in range(12):
        remote = random.choice(["remote", "hybrid", "onsite"])
        days = 0 if remote == "remote" else random.choice([2, 3, 5])
        one_way = 0 if remote == "remote" else random.randint(15, 80)
        sample_jobs.append(dict(
            title=random.choice(titles),
            company=random.choice(companies),
            level=random.choice(["junior", "mid", "senior"]),
            employment_type="full_time",
            remote_policy=remote,
            pay_usd_min=random.randint(90, 130) * 1000,
            pay_usd_max=random.randint(110, 160) * 1000,
            location_city="Remote" if remote == "remote" else "Somewhere KY",
            location_state="" if remote == "remote" else "KY",
            days_in_office_per_week=days,
            one_way_commute_miles=one_way,
            manual_match=random.randint(5, 9),
            skills="Python, SQL, pandas",
        ))

    job_ids = []
    for job in sample_jobs:
        jid = add_job(**job)
        job_ids.append(jid)
    print(f"✓ {len(job_ids)} sample jobs created")

    # 4. Create applications with a realistic timeline
    statuses_progression = [
        ("saved", None, None),
        ("applied", days_ago(28), days_ago(21)),
        ("applied", days_ago(21), days_ago(14)),
        ("interviewing", days_ago(18), days_ago(10)),
        ("interviewing", days_ago(14), days_ago(7)),
        ("offered", days_ago(12), None),
        ("rejected_employer", days_ago(20), None),
        ("rejected_self", days_ago(15), None),
        ("applied", days_ago(7), days_ago(2)),
        ("saved", None, None),
    ]

    for i, jid in enumerate(job_ids[:len(statuses_progression)]):
        status, applied, follow = statuses_progression[i]
        app_id = add_application(
            job_id=jid,
            status=status,
            applied_date=applied,
            next_follow_up=follow,
            notes=f"Sample application #{i+1}",
        )
        # bump a couple to higher interview stages
        if status == "interviewing":
            update_application(app_id, interview_stage=random.randint(1, 2))
        if status == "offered":
            update_application(app_id, interview_stage=3, offer_date=days_ago(5), offer_pay=142000)

    print(f"✓ Sample applications created with mixed statuses")

    print("\n=== Sample data ready! ===")
    print(f"Database : {SAMPLE_DB}")

    # Build viz.py and point it at this database + samples/sample_plots/
    # add the plotting calls at the bottom of this file


if __name__ == "__main__":
    generate()