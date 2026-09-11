"""
python/report.py
----------------
Generate weekly HTML reports for Star Hound Tracker.

Creates:
  weekly_report_YYYY-MM-DD.html         → editable (file paths)
  weekly_report_YYYY-MM-DD_export.html  → shareable (base64 embeds)
  weekly_report_YYYY-MM-DD_email.html   → email-ready (cid: images)
"""

from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from python.db import get_connection

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
    matches = sorted(chart_dir.glob(f"{name}*.png"))
    return matches[-1] if matches else None


def get_chart_files(sample: bool = False) -> dict[str, Path]:
    """Return chart name → actual PNG path on disk."""
    base = SAMPLE_PLOTS_DIR if sample else REAL_PLOTS_DIR
    chart_dir = _newest_day_folder(base)
    if chart_dir is None:
        return {}

    files = {}
    for name in CHART_NAMES:
        path = _latest_chart_file(chart_dir, name)
        if path:
            files[name] = path
    return files


def image_to_data_uri(path: Path | str | None) -> str:
    if not path:
        return ""

    path = Path(path)
    if not path.exists():
        return ""

    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "image/png")

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _chart_srcs(
    mode: str,
    sample: bool = False,
    report_dir: Path | None = None,
) -> dict[str, str]:
    """
    mode:
      file  → relative file path
      embed → base64 data URI
      email → cid:chart_name
    """
    files = get_chart_files(sample=sample)
    srcs = {name: "" for name in CHART_NAMES}

    for name, path in files.items():
        if mode == "email":
            srcs[name] = f"cid:{name}"
        elif mode == "embed":
            srcs[name] = image_to_data_uri(path)
        else:
            if report_dir is not None:
                srcs[name] = Path(os.path.relpath(path, start=report_dir)).as_posix()
            else:
                srcs[name] = path.as_posix()

    return srcs


def _img_tag(src: str, alt: str) -> str:
    if not src:
        return f"<p><em>No {alt} chart found.</em></p>"
    return f'<img src="{src}" alt="{alt}">'


def _read_sql(query: str, sample: bool = False) -> pd.DataFrame:
    db_path = SAMPLE_DB if sample else None
    with get_connection(db_path) as conn:
        return pd.read_sql(query, conn)


def build_context(
    sample: bool = False,
    report_dir: Path | None = None,
    charts_mode: str = "file",
) -> dict:
    now = datetime.now()

    user_df = _read_sql("SELECT name FROM user LIMIT 1", sample=sample)
    name = user_df["name"].iloc[0] if not user_df.empty else "Unknown"

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

    top_jobs_df = _read_sql(
        """
        SELECT title, company, job_score AS score
        FROM applications
        WHERE archived = 0 AND job_score IS NOT NULL
        ORDER BY job_score DESC
        LIMIT 10
        """,
        sample=sample,
    )
    top_jobs = top_jobs_df.to_dict(orient="records")

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
        "report_title": "Weekly Jobs Report",
        "name": name,
        "generated_on": now.strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "total_applications": total_apps,
            "interviews": interviews,
            "offers": offers,
            "avg_job_score": avg_score,
            "interview_rate": interview_rate,
        },
        "charts": _chart_srcs(charts_mode, sample=sample, report_dir=report_dir),
        "top_jobs": top_jobs,
        "followups_due": followups_due,
    }


def render_report(context: dict) -> str:
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
        header {{ margin-bottom: 32px; }}
        section {{ margin-bottom: 36px; }}
        img {{
            display: block;
            width: 100%;
            max-width: 720px;
            margin: 16px 0;
            border: 1px solid #ddd;
        }}
        ul {{ line-height: 1.7; }}
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
            {_img_tag(charts['status_breakdown'], 'Status breakdown')}
            {_img_tag(charts['apps_over_time'], 'Applications over time')}
            {_img_tag(charts['interview_rate'], 'Interview rate')}
            {_img_tag(charts['interview_quality'], 'Interview quality')}
            {_img_tag(charts['funnel'], 'Application funnel')}
        </section>
        <section>
            <h2>Highlights</h2>
            <h3>Top Jobs</h3>
            <ul>{top_jobs_html}</ul>
            <h3>Follow-ups Due</h3>
            <ul>{followups_html}</ul>
        </section>
    </main>
</body>
</html>
"""


def generate_report(sample: bool = False) -> dict[str, Path]:
    base = SAMPLE_REPORTS_DIR if sample else REAL_REPORTS_DIR
    today = datetime.now().strftime("%Y-%m-%d")
    day_folder = base / today
    day_folder.mkdir(parents=True, exist_ok=True)

    paths = {}
    for mode, suffix in (("file", ""), ("embed", "_export"), ("email", "_email")):
        context = build_context(sample=sample, report_dir=day_folder, charts_mode=mode)
        filename = day_folder / f"weekly_report_{today}{suffix}.html"
        filename.write_text(render_report(context), encoding="utf-8")
        paths[mode] = filename
        print(f"✓ {mode:5} report → {filename}")

    return paths


if __name__ == "__main__":
    generate_report(sample=True)