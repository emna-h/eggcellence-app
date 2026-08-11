#  Eggcellence

A full-stack egg quality control and analytics web application, built as an academic project at **PGH (Polina Group Holding)**, Tunis.

Eggcellence helps quality inspectors log laboratory measurements for egg samples (weight, height, freshness, shell strength, and grade) and gives administrators visibility into defect trends across departments and suppliers.

---

## Overview

Eggs are graded using standardized lab measurements — weight, albumen height, coloration, freshness (Haugh Unit), and shell strength. Eggcellence digitizes this process: inspectors log samples directly from the floor, and the system organizes that data for tracking and reporting, replacing manual paper logs and spreadsheets.

---

## Features

- **Fast data entry** — a streamlined form for logging shell grade, cracks, and freshness readings on the spot
- **Role-based dashboards** — separate experiences for Quality Inspectors (data entry) and Admins (analytics and oversight)
- **Grading reference panel** — built-in quality standards (Grade AA/A/B/C thresholds) and a measurement glossary, always visible during inspection
- **Inspection history** — a live, filterable log of samples with the ability to review or delete entries
- **Automated data pipelines** *(planned)* — SSIS-powered cleaning and defect-rate calculation
- **Executive analytics** *(planned)* — Power BI dashboards comparing department metrics and supplier trends

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Database | Microsoft SQL Server |
| ETL / Data Pipelines | SSIS (SQL Server Integration Services) |
| Analytics & Reporting | Power BI |

---

## Project Status

🚧 **In active development.**
- [x] Reset Password page
- [x] Login / sign up page
- [x] Landing page
- [x] User (inspector) dashboard — data entry form, inspection history, grading reference panel
- [ ] Admin dashboard — analytics and supplier oversight
- [ ] Backend API (authentication, data persistence)
- [ ] SQL Server database schema
- [ ] SSIS data pipelines
- [ ] Power BI reports
