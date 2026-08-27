"""
python/report.py
----------------
Generate a simple HTML weekly report for Star Hound Tracker.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from python.db import get_connection

# Paths
REAL_DB = Path("data/jobs.db")
SAMPLE_DB = Path("samples/sample_jobs.db")
REAL_PLOTS_DIR = Path("plots")
SAMPLE_PLOTS_DIR = Path("samples/sample_plots")
REAL_REPORTS_DIR = Path("reports")
SAMPLE_REPORTS_DIR = Path("samples/sample_reports")

CHART_NAMES = [
    "status_breakdown",
    "apps_over_time",
    "interview_rate",
    "interview_quality",
    "funnel",
]


def _newest_day_folder(base: Path) -> Path | None:
    """Return the newest YYYY-MM-DD subfolder, or None if none exist."""
    if not base.exists():
        return None

    valid = []
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        try:
            datetime.strptime(folder.name, "%Y-%m-%d")
            valid.append(folder)
        except ValueError:
            continue

    if not valid:
        return None

    return max(valid, key=lambda p: p.name)


def _latest_chart_file(chart_dir: Path, name: str) -> Path | None:
    """
    Find the newest file that starts with the chart name.
    Matches:
      status_breakdown.png
      status_breakdown_221010.png
    """
    matches = sorted(chart_dir.glob(f"{name}*.png"))
    if not matches:
        return None
    return matches[-1]


def _chart_paths(sample: bool = False, report_dir: Path | None = None) -> dict[str, str]:
    base = SAMPLE_PLOTS_DIR if sample else REAL_PLOTS_DIR
    chart_dir = _newest_day_folder(base)

    if chart_dir is None:
        return {name: "" for name in CHART_NAMES}

    paths = {}
    for name in CHART_NAMES:
        image_path = _latest_chart_file(chart_dir, name)
        if image_path is None:
            paths[name] = ""
            continue

        if report_dir is not None:
            paths[name] = Path(os.path.relpath(image_path, start=report_dir)).as_posix()
        else:
            paths[name] = image_path.as_posix()

    return paths


def _read_sql(query: str, sample: bool = False) -> pd.DataFrame:
    """Run a query against the correct database."""
    db_path = SAMPLE_DB if sample else None  # None = real DB
    with get_connection(db_path) as conn:
        return pd.read_sql(query, conn)


def build_context(sample: bool = False, report_dir: Path | None = None) -> dict:
    now = datetime.now()

    # 1. User name
    user_df = _read_sql("SELECT name FROM user LIMIT 1", sample=sample)
    name = user_df["name"].iloc[0] if not user_df.empty else "Unknown"

    # 2. Application stats
    stats_df = _read_sql(
        """
        SELECT
            COUNT(*) AS total_applications,
            SUM(CASE WHEN status IN ('interviewing', 'offered', 'accepted')
                      OR interview_stage >= 1 THEN 1 ELSE 0 END) AS interviews,
            SUM(CASE WHEN status IN ('offered', 'accepted') THEN 1 ELSE 0 END) AS offers,
            AVG(job_score) AS avg_job_score
        FROM applications
        WHERE archived = 0
        """,
        sample=sample,
    )

    total_apps = int(stats_df["total_applications"].iloc[0] or 0)
    interviews = int(stats_df["interviews"].iloc[0] or 0)
    offers = int(stats_df["offers"].iloc[0] or 0)
    avg_score = round(float(stats_df["avg_job_score"].iloc[0] or 0), 1)
    interview_rate = f"{(interviews / total_apps * 100):.1f}%" if total_apps else "0%"

    # 3. Top jobs
    top_jobs_df = _read_sql(
        """
        SELECT title, company, job_score AS score
        FROM applications
        WHERE archived = 0 AND job_score IS NOT NULL
        ORDER BY job_score DESC
        LIMIT 5
        """,
        sample=sample,
    )
    top_jobs = top_jobs_df.to_dict(orient="records")

    # 4. Follow-ups
    followups_df = _read_sql(
        """
        SELECT title, company, next_follow_up AS date
        FROM applications
        WHERE archived = 0
          AND next_follow_up IS NOT NULL
        ORDER BY next_follow_up ASC
        LIMIT 5
        """,
        sample=sample,
    )
    followups_due = followups_df.to_dict(orient="records")

    return {
        "report_title": "Star Hound Tracker – Weekly Report",
        "name": name,
        "generated_on": now.strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "total_applications": total_apps,
            "interviews": interviews,
            "offers": offers,
            "avg_job_score": avg_score,
            "interview_rate": interview_rate,
        },
        "charts": _chart_paths(sample=sample, report_dir=report_dir),
        "top_jobs": top_jobs,
        "followups_due": followups_due,
    }


def render_report(context: dict) -> str:
    """Turn the context dictionary into an HTML string."""
    stats = context["stats"]
    charts = context["charts"]

    top_jobs_html = "".join(
        f"<li>{job['title']} @ {job['company']} — {job['score']}</li>"
        for job in context["top_jobs"]
    ) or "<li>No jobs yet.</li>"

    followups_html = "".join(
        f"<li>{item['title']} @ {item['company']} — due {item['date']}</li>"
        for item in context["followups_due"]
    ) or "<li>No follow-ups due.</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context['report_title']}</title>
    <style>
        body {{
            box-sizing: border-box;
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 24px;
            color: #222;
        }}
        header {{
            margin-bottom: 32px;
        }}
        section {{
            margin-bottom: 36px;
        }}
        img {{
            display: block;
            width: 100%;
            max-width: 720px;
            margin: 16px 0;
            border: 1px solid #ddd;
        }}
        ul {{
            line-height: 1.7;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{context['report_title']}</h1>
        <h2>{context['name']}</h2>
        <p>Generated on: {context['generated_on']}</p>
    </header>

    <main>
        <section>
            <h2>Stats</h2>
            <ul>
                <li>Applications: {stats['total_applications']}</li>
                <li>Interviews: {stats['interviews']}</li>
                <li>Offers: {stats['offers']}</li>
                <li>Average Job Score: {stats['avg_job_score']}</li>
                <li>Interview Rate: {stats['interview_rate']}</li>
            </ul>
        </section>

        <section>
            <h2>Charts</h2>
            <img src="{charts['status_breakdown']}" alt="Status breakdown">
            <img src="{charts['apps_over_time']}" alt="Applications over time">
            <img src="{charts['interview_rate']}" alt="Interview rate">
            <img src="{charts['interview_quality']}" alt="Interview quality">
            <img src="{charts['funnel']}" alt="Application funnel">
        </section>

        <section>
            <h2>Highlights</h2>
            <h3>Top Jobs</h3>
            <ul>
                {top_jobs_html}
            </ul>

            <h3>Follow-ups Due</h3>
            <ul>
                {followups_html}
            </ul>
        </section>
    </main>
</body>
</html>
"""


def generate_report(sample: bool = False) -> Path:
    """
    Build the report and save it as an HTML file.

    sample=False → reports/YYYY-MM-DD/
    sample=True  → samples/sample_reports/YYYY-MM-DD/
    """
    base = SAMPLE_REPORTS_DIR if sample else REAL_REPORTS_DIR
    day_folder = base / datetime.now().strftime("%Y-%m-%d")
    day_folder.mkdir(parents=True, exist_ok=True)

    context = build_context(sample=sample, report_dir=day_folder)
    html = render_report(context)

    filename = day_folder / f"weekly_report_{datetime.now().strftime('%Y-%m-%d')}.html"
    filename.write_text(html, encoding="utf-8")

    print(f"✓ Report saved → {filename}")
    return filename


if __name__ == "__main__":
    generate_report(sample=True)