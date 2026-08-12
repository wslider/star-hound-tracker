# Star Hound Tracker

<p align="center">
  <img src="images/star_hound_tracker_logo_v1.png" alt="Star Hound Tracker Logo" width="320">
</p>

Local-first job search tracker. Score opportunities, manage your application pipeline, and (later) generate tailored resumes and weekly reports.

**Author:** William Slider  
**Status:** Early development / Version 1 in progress  
**License:** MIT

---

## Overview

Star Hound Tracker helps you:

- Log and score job opportunities
- Track applications from saved → applied → interview → offer
- Factor in pay, commute, and fit when prioritizing
- Avoid re-applying to rejected roles
- Visualize progress over time

Everything runs locally. Your data stays on your machine.

---

## Features

### Version 1 (current target)
- [ ] User profile (home location + pay preferences)
- [ ] Manual job entry
- [ ] Job scoring (pay, weekly commute, manual fit 1–10)
- [ ] Remote / hybrid / onsite commute handling
- [ ] Application pipeline with clear statuses
- [ ] Follow-up reminders
- [ ] Basic charts (applications, outcomes, scores)
- [ ] CSV storage under `data/`

### Version 2 (planned)
- [ ] URL / scrape-assisted job intake
- [ ] Expanded skills & preferences profile
- [ ] Tailored resume generation per job
- [ ] Weekly HTML/PDF reports
- [ ] Stronger automated fit signals

---

## Screenshots

_Coming soon._

<!-- Add plots or UI captures under images/ and link them here -->

---

## Tech stack

- Python 3.14.4
- pandas (data handling)
- matplotlib / seaborn (charts)
- geopandas 
- Jupyter notebook for prototyping
- CSV storage (SQLite possible later)

_Optional later:_ scraping libraries, HTML/PDF resume & report tooling

---

## Project structure

```text
├── job_tracker.ipynb      # Prototyping
├── job_tracker.py         # Main entry point
├── python/                # Modules (scoring, storage, viz, ...)
├── data/                  # Local CSVs (gitignored)
├── plots/                 # Generated charts (gitignored)
├── resumes/               # V2 – generated resumes
├── reports/               # V2 – weekly reports
├── images/
│   └── star_hound_tracker_logo_v1.png
├── notes.md               # Design notes
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd star-hound-tracker   # or your folder name

# (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> `data/`, `plots/`, `resumes/`, and `reports/` are created by the program when needed.

---

## Usage

### Notebook (development)
```bash
jupyter notebook job_tracker.ipynb
```

### Script (planned)
```bash
python job_tracker.py
```

Typical V1 flow:
1. Set or update your user profile (home lat/lon, pay preferences)
2. Add jobs manually
3. Review scores and move roles into the applications pipeline
4. Update status and follow-up dates as you progress
5. Generate charts when you want a snapshot

_Detailed CLI/menu commands will be documented here as they land._

---

## Scoring (V1)

Jobs are scored from three factors:

| Factor            | Source                                      |
|-------------------|---------------------------------------------|
| Pay               | Listing vs your preferred range             |
| Weekly commute    | Round-trip miles × days in office per week  |
| Fit               | Manual 1–10 match to skills / background    |

Remote roles use `0` commute days. Hybrid uses expected office days.  
Component scores are stored so weights can be tuned later.

---

## Data & privacy

- All data is stored **locally** (CSV files under `data/`)
- `data/`, `plots/`, `resumes/`, and `reports/` should remain gitignored
- Do not commit personal info, resumes, or scraped listing dumps

---

## Roadmap

See [`notes.md`](notes.md) for full schema, column types, and design decisions.

**Near term**
- Lock V1 schemas (`user`, `jobs`, `applications`)
- Implement scoring + CRUD flows
- Follow-ups + first charts

**Later**
- Scrape-assisted intake
- Resume generation
- Weekly reports

---

## Contributing

Personal project for now. Suggestions and issue reports are welcome if the repo is public.

---

## License

MIT License

Copyright (c) 2026 William Slider