"""
python/viz.py
-------------
Visualization module for Star Hound Tracker.

Supports both real data and sample/demo data.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from python.db import get_connection

# Default locations
REAL_PLOTS_DIR = Path("plots")
SAMPLE_PLOTS_DIR = Path("samples/sample_plots")
SAMPLE_DB = Path("samples/sample_jobs.db")


# Shared helpers 

# Return the correct plots folder and make sure the day subfolder exists.
def _get_output_dir(sample: bool = False) -> Path:
    base = SAMPLE_PLOTS_DIR if sample else REAL_PLOTS_DIR
    day_folder = base / datetime.now().strftime("%Y-%m-%d")
    day_folder.mkdir(parents=True, exist_ok=True)
    return day_folder

# Save a figure with a timestamped filename and close it.
def _save_fig(fig: plt.Figure, name: str, sample: bool = False) -> Path:
    output_dir = _get_output_dir(sample)
    timestamp = datetime.now().strftime("%H%M%S")
    filename = output_dir / f"{name}_{timestamp}.png"

    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Saved {filename}")
    return filename

# Run a query against the correct database.
def _read_sql(query: str, sample: bool = False) -> pd.DataFrame:
    db_path = SAMPLE_DB if sample else None  # None = real DB
    with get_connection(db_path) as conn:
        return pd.read_sql(query, conn)



# Individual charts

def plot_status_breakdown(sample: bool = False) -> Path:
    """Bar chart of current application statuses."""
    df = _read_sql("""
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE archived = 0
        GROUP BY status
        ORDER BY count DESC
    """, sample=sample)

    if df.empty:
        print("No application data for status breakdown.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df, x="status", y="count", ax=ax, palette="Blues_d")
    ax.set_title("Application Status Breakdown")
    ax.set_xlabel("")
    ax.set_ylabel("Count")
    sns.despine()
    plt.xticks(rotation=30, ha="right")

    return _save_fig(fig, "status_breakdown", sample=sample)


def plot_applications_over_time(sample: bool = False) -> Path:
    """Cumulative applications over time."""
    df = _read_sql("""
        SELECT applied_date, COUNT(*) AS apps
        FROM applications
        WHERE applied_date IS NOT NULL
        GROUP BY applied_date
        ORDER BY applied_date
    """, sample=sample)

    if df.empty:
        print("No application dates found.")
        return None

    df["applied_date"] = pd.to_datetime(df["applied_date"])
    df["cumulative"] = df["apps"].cumsum()

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(df["applied_date"], df["cumulative"], marker="o", linewidth=2)
    ax.set_title("Cumulative Applications Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Applications")
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    fig.autofmt_xdate()

    return _save_fig(fig, "apps_over_time", sample=sample)


def plot_interview_rate_over_time(sample: bool = False) -> Path:
    """Simple monthly interview rate (% of applications that reached interviewing+)."""
    df = _read_sql("""
        SELECT
            strftime('%Y-%m', applied_date) AS month,
            COUNT(*) AS total_apps,
            SUM(CASE WHEN status IN ('interviewing', 'offered', 'accepted')
                     OR interview_stage >= 1 THEN 1 ELSE 0 END) AS interviews
        FROM applications
        WHERE applied_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """, sample=sample)

    if df.empty or df["total_apps"].sum() == 0:
        print("Not enough data for interview rate.")
        return None

    df["interview_rate"] = (df["interviews"] / df["total_apps"] * 100).round(1)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(df["month"], df["interview_rate"], marker="o", color="green", linewidth=2)
    ax.set_title("Interview Rate Over Time (%)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Interview Rate %")
    ax.set_ylim(0, 100)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.xticks(rotation=45, ha="right")

    return _save_fig(fig, "interview_rate", sample=sample)


def plot_interview_quality(sample: bool = False) -> Path:
    """Average job_score of roles that reached interview stage vs all applications."""
    df = _read_sql("""
        SELECT
            CASE
                WHEN status IN ('interviewing', 'offered', 'accepted')
                     OR interview_stage >= 1 THEN 'Interviewed'
                ELSE 'All Applications'
            END AS category,
            AVG(job_score) AS avg_score
        FROM applications
        WHERE job_score IS NOT NULL
        GROUP BY category
    """, sample=sample)

    if df.empty:
        print("No score data available.")
        return None

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=df, x="category", y="avg_score", ax=ax, palette="viridis")
    sns.despine()
    ax.set_title("Average Job Score: Interviewed vs All")
    ax.set_ylabel("Average Job Score")
    ax.set_xlabel("")

    return _save_fig(fig, "interview_quality", sample=sample)


def plot_funnel_summary(sample: bool = False) -> Path:
    """Simple funnel-style counts."""
    df = _read_sql("""
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE archived = 0
        GROUP BY status
    """, sample=sample)

    if df.empty:
        print("No data for funnel.")
        return None

    # Order the funnel stages
    order = ["saved", "applied", "interviewing", "offered", "accepted",
             "rejected_employer", "rejected_self", "withdrawn"]
    df["status"] = pd.Categorical(df["status"], categories=order, ordered=True)
    df = df.sort_values("status")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df, x="count", y="status", ax=ax, palette="magma")
    sns.despine()
    ax.set_title("Application Funnel")
    ax.set_xlabel("Count")
    ax.set_ylabel("")

    return _save_fig(fig, "funnel_summary", sample=sample)


# ----------------------------------------------------------------------
# Main entry points
# ----------------------------------------------------------------------

def generate_visualizations(sample: bool = False) -> None:
    """Generate all charts for either real or sample data."""
    label = "SAMPLE" if sample else "REAL"
    print(f"\n=== Generating {label} visualizations ===\n")

    plot_status_breakdown(sample=sample)
    plot_applications_over_time(sample=sample)
    plot_interview_rate_over_time(sample=sample)
    plot_interview_quality(sample=sample)
    plot_funnel_summary(sample=sample)

    print("\nDone.")


if __name__ == "__main__":
    # Default to sample data while you’re still building / testing
    generate_visualizations(sample=True)