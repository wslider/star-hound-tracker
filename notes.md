# Star Hound Tracker

Personal job-search tracker that scores opportunities, tracks the application pipeline, and (in later versions) helps tailor resumes and produce weekly reports.

Local-first. CSV storage in V1. Designed to grow without rewriting the core model.

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
- Simple charts
- All data local (CSV)

### Data model

#### `user` table
Single-row profile for scoring and commute logic.

| Column              | Datatype | Notes |
|---------------------|----------|--------|
| user_id             | int      | Primary key (usually `1`) |
| city                | str      | Home city |
| state               | str      | Home state |
| lat                 | float    | Home latitude |
| lon                 | float    | Home longitude |
| preferred_pay_min   | float    | Optional target floor (annual or normalized unit) |
| preferred_pay_max   | float    | Optional target ceiling |
| max_weekly_commute_miles | float | Soft preference / scoring reference (optional) |
| notes               | str      | Free text |

**Storage:** `data/user.csv`

---

#### `jobs` table
Opportunity pool (jobs you might apply to).

| Column                  | Datatype | Notes |
|-------------------------|----------|--------|
| job_id                  | str/int  | Primary key (UUID or incremental) |
| title                   | str      | Job title |
| company                 | str      | Company name |
| level                   | str      | e.g. `junior`, `mid`, `senior`, `staff` (normalize) |
| employment_type         | str      | `full_time`, `part_time`, `contract`, `internship` |
| remote_policy           | str      | `onsite`, `hybrid`, `remote` |
| pay_min                 | float    | Lower end of range (use same unit everywhere) |
| pay_max                 | float    | Upper end of range (nullable if unknown) |
| pay_type                | str      | `salary`, `hourly` (normalize before scoring if mixed) |
| location_city           | str      | Office / listed city |
| location_state          | str      | |
| office_lat              | float    | Nullable; required for accurate commute if not remote |
| office_lon              | float    | Nullable |
| days_in_office_per_week | float    | `0` for remote; `1–5` for hybrid/onsite |
| one_way_commute_miles   | float    | Manual or calculated; `0` if remote |
| weekly_commute_miles    | float    | Derived: `one_way_commute_miles * 2 * days_in_office_per_week` |
| skills                  | str      | Comma-separated or JSON-like list (V1 simple string OK) |
| manual_match            | int      | **1–10** user estimate of skill/level/background fit |
| job_score               | float    | Final weighted score (0–100 recommended) |
| score_pay               | float    | Component score (for transparency / tuning) |
| score_commute           | float    | Component score |
| score_match             | float    | Component score |
| source_url              | str      | Listing URL (nullable in pure manual mode) |
| date_posted             | str      | ISO date `YYYY-MM-DD` (nullable) |
| date_added              | str      | ISO date when you added it |
| raw_data_path           | str      | Path to saved full text / notes file (nullable in V1) |
| notes                   | str      | Free text |

**Storage:** `data/jobs.csv`  
**Local raw dumps (optional):** `data/raw/`

---

#### `applications` table
Pipeline of jobs you plan to apply to, have applied to, or have finished.

| Column            | Datatype | Notes |
|-------------------|----------|--------|
| application_id    | str/int  | Primary key |
| job_id            | str/int  | FK → jobs.job_id |
| title             | str      | Denormalized for readable CSV (optional but handy) |
| company           | str      | Denormalized |
| job_score         | float    | Snapshot at time of tracking (or joined live) |
| status            | str      | See status values below |
| applied_date      | str      | ISO date (nullable until applied) |
| last_contact_date | str      | ISO date |
| next_follow_up    | str      | ISO date – drives reminders |
| interview_stage   | int      | `0` = none, `1` = first, `2` = second, … |
| offer_date        | str      | ISO date (nullable) |
| offer_pay         | float    | Actual offer if different from listing |
| rejected_by       | str      | `employer`, `self`, or empty |
| notes             | str      | Interview notes, contacts, etc. |
| archived          | bool/int | `0/1` – hide from active views without deleting |

**Recommended `status` values (use one field, not many booleans):**  
`saved` | `applied` | `interviewing` | `offered` | `accepted` | `rejected_employer` | `rejected_self` | `withdrawn`

**Rejection policy (V1):**  
Keep the row. Set status to `rejected_*` (and optionally `archived = 1`).  
Do **not** delete – preserves history and prevents accidental re-apply.  
Active views sort by `job_score` desc and filter out terminal/archived statuses as needed.

**Storage:** `data/applications.csv`

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

---

### V1 features

#### Manual job entry
Python function(s) to:
- prompt or accept fields
- compute `weekly_commute_miles` and `job_score`
- append/update `data/jobs.csv`

#### Application tracking
- Link via `job_id`
- Update `status`, dates, `next_follow_up`, notes
- List active applications sorted by score / follow-up date

#### Follow-up reminders
Function that scans `applications` for:
- `next_follow_up <= today`
- post-application and post-interview cadences (user-set or simple defaults)

Output: console list or small checklist (calendar/email can wait).

#### Charts
Use matplotlib or seaborn. Write PNGs to `plots/`.

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
  user.csv
  jobs.csv
  applications.csv
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

#### `user` table (extended)
| Column           | Datatype | Notes |
|------------------|----------|--------|
| skills           | str/JSON | List of skills |
| experience_summary | str    | Short background text |
| experience_years | float    | Optional |
| preferences      | str/JSON | Schedule, remote preference, must-have skills, etc. |
| resume_base_path | str      | Path to master resume / template data |

#### `jobs` table (extended)
| Column              | Datatype | Notes |
|---------------------|----------|--------|
| scraped_keywords    | str/JSON | Keywords extracted from listing |
| raw_html_path / raw_text_path | str | Full saved listing |
| fit_score_auto      | float    | Optional automated skill overlap score |
| last_scraped        | str      | ISO datetime |

Manual `manual_match` can remain as an override or blend with `fit_score_auto`.

#### New supporting ideas (optional)
- `skills` reference list or simple junction later if you outgrow comma-separated strings
- Dedup key (company + title + location hash) to avoid duplicate jobs from multiple sources

---

### V2 features

#### Job intake
- **Manual** (still supported for odd listings)
- **URL input** → scrape title, company, pay, location, description, keywords  
- Review/edit before commit to `jobs` table  
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
- Pull charts + summary stats (applied, response rate, interviews, top open scores, follow-ups due)
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
│   ├── storage.py           # load/save CSVs (later SQLite)
│   ├── models.py            # column helpers / validation
│   ├── scoring.py           # commute + weighted score
│   ├── jobs.py              # add/update/list jobs
│   ├── applications.py      # pipeline + status updates
│   ├── reminders.py         # follow-up scan
│   ├── viz.py               # charts
│   ├── scrape.py            # V2
│   ├── resume.py            # V2
│   └── report.py            # V2
├── data/                    # created at runtime (gitignored)
├── plots/                   # created at runtime
├── resumes/                 # V2
└── reports/                 # V2
```

`.gitignore` should include at least: `data/`, `plots/`, `resumes/`, `reports/`, local config with personal info, `__pycache__/`, `.ipynb_checkpoints/`.

---

## Implementation order (recommended)

**V1 MVP**
1. Create `data/` + empty CSVs with headers  
2. User profile load/save  
3. Add job (manual) + commute calculation + score  
4. Applications CRUD + status updates  
5. List top jobs / active applications  
6. Follow-up scan  
7. A few charts  

**Then V2**
8. URL scrape + review step  
9. Expand user profile  
10. Keyword extraction + optional auto fit  
11. Resume generator  
12. Weekly report generator  

---

## Design principles
- Prefer **status + dates** over many independent booleans.
- **Never delete** rejected jobs; archive or filter.
- Store **score components** so weights can be tuned.
- Keep V1 useful without scraping or NLP.
- Normalize enums early (`remote_policy`, `status`, `level`, `employment_type`).
- Everything personal stays local and gitignored.
