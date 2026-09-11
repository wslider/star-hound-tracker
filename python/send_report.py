"""
python/send_report.py
---------------------
Email the latest email-ready HTML report with CID chart attachments.

Uses EMAIL_USER and EMAIL_PASS from the environment.
Gmail: EMAIL_PASS should be an App Password.
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from python.report import (
    REAL_REPORTS_DIR,
    SAMPLE_REPORTS_DIR,
    get_chart_files,
)

REPORTS_DIR = REAL_REPORTS_DIR


def find_latest_email_html(base: Path) -> Path | None:
    if not base.exists():
        return None

    day_folders = []
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        try:
            datetime.strptime(folder.name, "%Y-%m-%d")
            day_folders.append(folder)
        except ValueError:
            continue

    if not day_folders:
        return None

    newest = max(day_folders, key=lambda p: p.name)
    matches = sorted(newest.glob("*_email.html"))
    return matches[-1] if matches else None


def send_report(sample: bool = False, to_email: str | None = None) -> bool:
    from_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    to_email = to_email or from_email

    if not from_email or not password:
        print("Missing EMAIL_USER or EMAIL_PASS environment variables.")
        return False

    base = SAMPLE_REPORTS_DIR if sample else REPORTS_DIR
    html_path = find_latest_email_html(base)
    if html_path is None:
        print(f"No *_email.html found in {base}. Generate a report first.")
        return False

    charts = get_chart_files(sample=sample)
    html = html_path.read_text(encoding="utf-8")

    msg = MIMEMultipart("related")
    msg["Subject"] = "Star Hound Tracker – Weekly Report"
    msg["From"] = from_email
    msg["To"] = to_email

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("Your weekly job-search report is included below.", "plain"))
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    for name, path in charts.items():
        with path.open("rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
        img.add_header("Content-ID", f"<{name}>")
        img.add_header("Content-Disposition", "inline", filename=path.name)
        msg.attach(img)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(from_email, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False

    print(f"✓ Sent {html_path.name} with {len(charts)} chart(s) to {to_email}")
    return True


if __name__ == "__main__":
    send_report(sample=False)