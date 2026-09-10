# Eggcellence — Egg Quality Control & Analytics Platform

A full-stack quality control system for tracking egg inspections, built for Poulina Group Holding (PGH).
Covers the entire pipeline: web app → OLTP database → SSIS ETL → data warehouse →
Power BI analytics.

## What this project actually is

Inspectors log daily egg quality samples (weight, height, coloration, freshness,
shell strength, grade) through a web dashboard. Admins manage inspectors, review
all logged samples, handle support tickets, and adjust grading thresholds. On top
of the live operational database, an SSIS pipeline periodically loads a separate
data warehouse (star schema), which Power BI reads for historical trend analysis.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS,JavaScript (`fetch` API) |
| Backend API | Python 3.12, Flask, session-based auth |
| OLTP Database | SQL Server (`EggcellenceDB`) |
| ETL | SQL Server Integration Services (SSIS), Visual Studio / SSDT |
| Data Warehouse | SQL Server (`DestinationDW`), star schema |
| BI / Reporting | Power BI Desktop |
| Email | SMTP (Gmail App Password), Python `smtplib` |

---

## Prerequisites :

- **Python 3.12** 
- **SQL Server** + **SSMS** (SQL Server Management Studio)
- **ODBC Driver 18 for SQL Server**
- **VS Code** with the **Live Server** extension (serves the frontend)
- **Visual Studio** with the **SQL Server Integration Services** workload (for the
  ETL packages) 
- **Power BI Desktop**

---

## Python dependencies

Everything the backend needs:

```
Flask==3.0.2
Flask-Cors==4.0.0
pyodbc
bcrypt==4.2.0
Werkzeug==3.0.1
python-dotenv==1.0.1
```

## Project structure

```
Eggcellence/
├── sql/                              ← run these in SSMS, in order
│   ├── 01_schema.sql                 ← core OLTP schema (users, inspections, etc.)
│   ├── 02_ssis_etl_procedure.sql     ← staging→production stored procedure
│   ├── 03_seed_data.sql              ← optional demo data
│   ├── 04_add_email_confirmation.sql ← adds email-confirmation tables (non-destructive)
│   ├── dw_01b_fact_tables_corrected.sql   ← warehouse: FactInspections, FactSupportTickets
│   ├── dw_02_support_tickets_fact.sql
│   ├── dw_03_grading_settings.sql
│   ├── dw_03b_fix_dimgradingsettings.sql
│   └── dw_04_fix_fact_tables.sql
├── backend/
│   ├── app.py                        ← Flask API, all routes
│   ├── db.py                         ← SQL Server connection helper
│   ├── email_utils.py                ← SMTP confirmation emails
│   ├── seed_users.py                 ← run once: sets real password hashes + access keys
│   ├── requirements.txt
│   └── .env                          
└── frontend/
    ├── landing.html + landing.css
    ├── Login.html + Login.css
    ├── VerifyRole.html + VerifyRole.css
    ├── ResetPassword.html + ResetPassword.css
    ├── contact.html + contact.css
    ├── UserDashboard.html + UserDashboard.css
    ├── admin.html + admin.css
    └── (image assets)
```

Separately, in its own Visual Studio solution: an **Integration Services Project**
containing the SSIS packages that load `DestinationDW`.

---

## Setup — full order of operations

### 1. Database (SSMS)
Run in this exact order, connected to the SQL Server instance:
1. `01_schema.sql`
2. `02_ssis_etl_procedure.sql`
3. `03_seed_data.sql` (optional — demo data)
4. `04_add_email_confirmation.sql`

### 2. Backend
```
pip install -r requirements.txt
python seed_users.py
``` 
**ADMIN_KEY = "Egg-Admin-2026!"
USER_KEY = "Egg-User-2026!**
every user / admin need to log in and to pass the security-key verification step.

Run the API:
```
python app.py
```
Runs on `http://127.0.0.1:5500`.

### 3. Frontend
In VS Code, right-click `frontend/landing.html` → **"Open with Live Server"**.
Opens on `http://127.0.0.1:5500`.

### 4. Data Warehouse (separate Visual Studio SSIS project)
1. Create the destination database tables by running the `dw_*.sql` scripts, in
   this order: `dw_01b_fact_tables_corrected.sql` → `dw_02_support_tickets_fact.sql`
   → `dw_03_grading_settings.sql` → `dw_03b_fix_dimgradingsettings.sql` →
   `dw_04_fix_fact_tables.sql`.
2. In Visual Studio, build the SSIS packages with connection managers `Source DB`
   (→ `EggcellenceDB`) and `Destination DW` (→ your warehouse database).
3. Control flow order: `Truncate_Tables → DimUsers → DimGradingSettings →
   DFT_FactInspections → FactSupportTickets`. `Dim_date` runs once, separately,
   and is never re-run (static calendar table).
4. Run the package (▶ Démarrer) any time you want the warehouse refreshed with
   the latest data from `EggcellenceDB`.

### 5. Power BI
1. Open Power BI Desktop → **Get Data → SQL Server** → connect to your
   `DestinationDW` database, Import mode.
2. Build/open `Eggcellence.pbix`
3. After every SSIS run, click **Refresh** in Power BI Desktop, then **Publish**
   again to push the update to your Power BI Service workspace .
4. The report is accessed from the admin dashboard via a plain button (same-tab
   navigation, not embedded)

---

## Running the whole thing, day to day

Three things need to be running simultaneously for the app itself to work:
1. **SQL Server** (runs as a background Windows service — normally always on)
2. **Flask**: `python app.py` (in `backend/`, with the venv active)
3. **Live Server** serving `frontend/` in VS Code


---

## Key architectural decisions worth knowing

- **Authentication**: Flask server-side sessions (signed cookie), not JWT — kept
  simple deliberately for this project's scope.
- **Access keys**: Real bcrypt-hashed keys stored in `access_keys`, rotated via
  `seed_users.py`.
- **Data warehouse refresh**: full truncate-and-reload on every SSIS run
- **Power BI**: kept as a fully separate deliverable from the live web app 
  
