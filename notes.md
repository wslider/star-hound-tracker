# Star Hound Tracker

Personal job-search tracker that scores opportunities, tracks the application pipeline, and (in later versions) helps tailor resumes and produce weekly reports.

Local-first. **SQLite is the source of truth in V1.**  
pandas + matplotlib/seaborn are used for analysis, plots, and reports.  
Designed to grow without rewriting the core model.

---

## Architecture

```text
User input / menu
  → SQL INSERT / UPDATE / SELECT on SQLite (data/jobs.db)
    → pandas (pd.read_sql) when analysis is needed
      → matplotlib / seaborn → plots/ and reports/
```

- **Writes & pipeline updates** → SQLite  
- **Visuals & reports** → query → DataFrame → plot  
- Enable foreign keys per connection: `PRAGMA foreign_keys = ON`

---

## High-level flow

1. Maintain a simple **user** profile (home location + preferences).
2. Add **jobs** (manual in V1; scrape-assisted in V2).
3. Compute a **job score** from pay, weekly commute, and fit.
4. Move promising jobs into **applications** and track status over time.
5. Surface follow-ups, charts, and (V2) tailored resumes + weekly reports.

---

## Version 1 – Core tracker

### Goals
- Manual job entry
- Location-aware scoring (pay + weekly commute + manual fit)
- Application pipeline tracking
- Rejection history (do not re-apply accidentally)
- Basic follow-up reminders
- Simple charts (SQL → pandas → matplotlib/seaborn)
- All data local (**SQLite**)

### Data model

Storage: single database file **`data/jobs.db`**  
Tables: `user`, `jobs`, `applications`

Suggested SQLite types:
- integers → `INTEGER`
- floats → `REAL`
- strings / dates / JSON-as-text → `TEXT`
- flags → `INTEGER` (`0`/`1`)

Dates stored as ISO text: `YYYY-MM-DD` (or full datetime when needed).

---

#### `user` table
Single-row profile for scoring and commute logic.

| Column                   | Datatype | Notes |
|--------------------------|----------|--------|
| user_id                  | INTEGER  | Primary key (usually `1`) |
| city                     | TEXT     | Home city |
| state                    | TEXT     | Home state |
| lat                      | REAL     | Home latitude |
| lon                      | REAL     | Home longitude |
| preferred_pay_min        | REAL     | Optional target floor (annual or normalized unit) |
| preferred_pay_max        | REAL     | Optional target ceiling |
| max_weekly_commute_miles | REAL     | Soft preference / scoring reference (optional) |
| notes                    | TEXT     | Free text |

---

#### `jobs` table
Opportunity pool (jobs you might apply to).

| Column                  | Datatype | Notes |
|-------------------------|----------|--------|
| job_id                  | TEXT     | Primary key (UUID or string id) |
| title                   | TEXT     | Job title |
| company                 | TEXT     | Company name |
| level                   | TEXT     | e.g. `junior`, `mid`, `senior`, `staff` (normalize) |
| employment_type         | TEXT     | `full_time`, `part_time`, `contract`, `internship` |
| remote_policy           | TEXT     | `onsite`, `hybrid`, `remote` |
| pay_min                 | REAL     | Lower end of range (use same unit everywhere) |
| pay_max                 | REAL     | Upper end of range (nullable if unknown) |
| pay_type                | TEXT     | `salary`, `hourly` (normalize before scoring if mixed) |
| location_city           | TEXT     | Office / listed city |
| location_state          | TEXT     | |
| office_lat              | REAL     | Nullable; needed for accurate commute if not remote |
| office_lon              | REAL     | Nullable |
| days_in_office_per_week | REAL     | `0` for remote; `1–5` for hybrid/onsite |
| one_way_commute_miles   | REAL     | Manual or calculated; `0` if remote |
| weekly_commute_miles    | REAL     | Derived: `one_way * 2 * days_in_office_per_week` |
| skills                  | TEXT     | Comma-separated or JSON text (V1 simple string OK) |
| manual_match            | INTEGER  | **1–10** user estimate of skill/level/background fit |
| job_score               | REAL     | Final weighted score (0–100 recommended) |
| score_pay               | REAL     | Component score (transparency / tuning) |
| score_commute           | REAL     | Component score |
| score_match             | REAL     | Component score |
| source_url              | TEXT     | Listing URL (nullable in pure manual mode) |
| date_posted             | TEXT     | ISO date `YYYY-MM-DD` (nullable) |
| date_added              | TEXT     | ISO date when you added it |
| raw_data_path           | TEXT     | Path to saved full text / notes file (nullable in V1) |
| notes                   | TEXT     | Free text |

**Local raw dumps (optional):** `data/raw/`

---

#### `applications` table
Pipeline of jobs you plan to apply to, have applied to, or have finished.

| Column            | Datatype | Notes |
|-------------------|----------|--------|
| application_id    | TEXT     | Primary key |
| job_id            | TEXT     | FK → `jobs.job_id` |
| title             | TEXT     | Optional denormalized copy (handy for quick lists) |
| company           | TEXT     | Optional denormalized copy |
| job_score         | REAL     | Snapshot at track time (or join live from `jobs`) |
| status            | TEXT     | See status values below |
| applied_date      | TEXT     | ISO date (nullable until applied) |
| last_contact_date | TEXT     | ISO date |
| next_follow_up    | TEXT     | ISO date – drives reminders |
| interview_stage   | INTEGER  | `0` = none, `1` = first, `2` = second, … |
| offer_date        | TEXT     | ISO date (nullable) |
| offer_pay         | REAL     | Actual offer if different from listing |
| rejected_by       | TEXT     | `employer`, `self`, or empty |
| notes             | TEXT     | Interview notes, contacts, etc. |
| archived          | INTEGER  | `0/1` – hide from active views without deleting |

**Recommended `status` values (one field, not many booleans):**  
`saved` | `applied` | `interviewing` | `offered` | `accepted` | `rejected_employer` | `rejected_self` | `withdrawn`

**Rejection policy (V1):**  
Keep the row. Set status to `rejected_*` (and optionally `archived = 1`).  
Do **not** delete – preserves history and prevents accidental re-apply.  
Active views sort by `job_score` desc and filter out terminal/archived statuses as needed.

**Foreign key:**  
`FOREIGN KEY (job_id) REFERENCES jobs(job_id)`  
Must enable: `PRAGMA foreign_keys = ON` on each connection.

---

### V1 scoring logic

**Inputs**
- Pay (vs `preferred_pay_min` / `preferred_pay_max` or a target)
- Weekly commute miles
- Manual match (1–10)

**Weekly commute**
```text
weekly_commute_miles = one_way_commute_miles * 2 * days_in_office_per_week
```
- `remote` → days = 0 → weekly miles = 0  
- `hybrid` → use expected office days  
- `onsite` → typically 5 (or whatever is realistic)

**Component ideas (normalize each to ~0–1 or 0–100)**
1. **Pay component** – higher when offer sits inside/above preferred range; penalize below floor.
2. **Commute component** – higher when weekly miles are low; falls as miles rise (remote scores best on this axis).
3. **Match component** – `manual_match / 10`.

**Final score (example weights – tune freely)**
```text
job_score = 100 * (
    0.40 * pay_norm +
    0.25 * commute_norm +
    0.35 * match_norm
)
```
Store the three component scores plus `job_score` on the job row.

Missing office location on hybrid/onsite → treat commute as incomplete (neutral or low) until filled.

Scoring runs in Python before `INSERT`/`UPDATE` (compute values, then write to SQLite).

---

### V1 features

#### Manual job entry
Python function(s) to:
- prompt or accept fields
- compute `weekly_commute_miles` and `job_score`
- `INSERT` into `jobs` (parameterized SQL)

#### Application tracking
- Link via `job_id`
- `UPDATE` `status`, dates, `next_follow_up`, notes
- List active applications with SQL (`ORDER BY job_score DESC`, filter status/archived)
- Optional `JOIN jobs` for live title/company/score

#### Follow-up reminders
SQL scan of `applications` for:
- `next_follow_up <= date('now')` (or pass today’s date from Python)
- post-application and post-interview cadences (user-set or simple defaults)

Output: console list or small checklist (calendar/email can wait).

#### Charts
1. `pd.read_sql(...)` from SQLite  
2. matplotlib / seaborn  
3. Write PNGs to `plots/`

Suggested V1 plots:
- Applications over time (count by week/month)
- Status breakdown (bar)
- Interview / offer rates
- Score distribution
- Pay ranges of tracked jobs
- Weekly commute vs score (scatter)

---

### V1 storage & folders created by the program
```text
data/
  jobs.db           # SQLite source of truth
  raw/              # optional text dumps
plots/              # png charts
```

---

## Version 2 – Automation & leverage

### Goals
- Scrape or URL-assisted job intake
- Richer user profile (skills, experience, preferences)
- Auto-suggest keywords / stronger fit signal
- Generate tailored resumes per job
- Weekly PDF/HTML reports with charts

### Data model additions / extensions

Same SQLite database; alter/extend tables as needed.

#### `user` table (extended)
| Column             | Datatype | Notes |
|--------------------|----------|--------|
| skills             | TEXT     | List of skills (JSON text OK) |
| experience_summary | TEXT     | Short background text |
| experience_years   | REAL     | Optional |
| preferences        | TEXT     | Schedule, remote preference, must-haves (JSON text OK) |
| resume_base_path   | TEXT     | Path to master resume / template data |

#### `jobs` table (extended)
| Column                | Datatype | Notes |
|-----------------------|----------|--------|
| scraped_keywords      | TEXT     | Keywords extracted from listing |
| raw_html_path         | TEXT     | Full saved listing (or raw_text_path) |
| fit_score_auto        | REAL     | Optional automated skill overlap score |
| last_scraped          | TEXT     | ISO datetime |

Manual `manual_match` can remain as an override or blend with `fit_score_auto`.

#### New supporting ideas (optional)
- `skills` reference table or junction if you outgrow string lists
- Dedup key (company + title + location hash) to avoid duplicate jobs from multiple sources

---

### V2 features

#### Job intake
- **Manual** (still supported for odd listings)
- **URL input** → scrape title, company, pay, location, description, keywords  
- Review/edit before `INSERT` into `jobs`  
- Respect site terms; prefer official APIs when available; treat scrape as best-effort

#### Stronger scoring
- Blend automated keyword/skill overlap with manual match
- Use expanded preferences (remote tolerance, must-have skills, etc.)

#### Resume generation
- Inputs: job row (keywords + description signals) + user profile
- Emphasize matching skills/experience
- Output: HTML and/or PDF  
- **Storage:** `resumes/` (e.g. `resumes/{job_id}_{company}.pdf`)

#### Weekly reports
- Pull charts + summary stats via SQL → pandas  
- Output: HTML or PDF  
- **Storage:** `reports/`

#### Follow-ups (enhanced)
- Same core dates; optional export to calendar or richer notification later

---

## Project structure

```text
star_hound_tracker/          # or repo root
├── job_tracker.ipynb        # prototype & exploration first
├── job_tracker.py           # main entry (CLI / menu)
├── README.md
├── .gitignore
├── requirements.txt
├── images/                  # static assets if any
├── python/                  # modules
│   ├── db.py                # connect, init schema, PRAGMA foreign_keys=ON
│   ├── models.py            # schema helpers / validation
│   ├── scoring.py           # commute + weighted score
│   ├── jobs.py              # add/update/list jobs (SQL)
│   ├── applications.py      # pipeline + status updates (SQL)
│   ├── reminders.py         # follow-up scan (SQL)
│   ├── viz.py               # read_sql → charts
│   ├── scrape.py            # V2
│   ├── resume.py            # V2
│   └── report.py            # V2
├── data/                    # created at runtime (gitignored)
│   └── jobs.db
├── plots/                   # created at runtime
├── resumes/                 # V2
└── reports/                 # V2
```

`.gitignore` should include at least: `data/`, `plots/`, `resumes/`, `reports/`, local config with personal info, `__pycache__/`, `.ipynb_checkpoints/`.

---

## Implementation order (recommended)

**V1 MVP**
1. Create `data/` + `init_db()` (`CREATE TABLE IF NOT EXISTS ...`)  
2. User profile insert/update/select  
3. Add job (manual) + commute calculation + score → `INSERT`  
4. Applications CRUD + status updates via SQL  
5. List top jobs / active applications (`SELECT` / `JOIN`)  
6. Follow-up scan  
7. A few charts (`pd.read_sql` → matplotlib/seaborn → `plots/`)

**Then V2**
8. URL scrape + review step  
9. Expand user profile  
10. Keyword extraction + optional auto fit  
11. Resume generator  
12. Weekly report generator  

---

## Design principles
- SQLite is the **source of truth**; pandas is for analysis and plotting.
- Prefer **status + dates** over many independent booleans.
- **Never delete** rejected jobs; archive or filter.
- Store **score components** so weights can be tuned.
- Keep V1 useful without scraping or NLP.
- Normalize enums early (`remote_policy`, `status`, `level`, `employment_type`).
- Use **parameterized SQL** (`?` placeholders) for all inputs.
- Enable **foreign keys** on every connection.
- Everything personal stays local and gitignored.