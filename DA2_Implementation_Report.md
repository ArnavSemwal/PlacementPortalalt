# DA2 Implementation Report & Testing Guide
**Course:** Database Management Systems (DBMS)  
**Project:** Campus Placement Portal  
**Phase:** DA2 (Core Implementation Deliverables)  

---

## 1. Migration Summary
As per the strict isolated workspace requirement, the project was migrated from SQLite to **PostgreSQL** entirely within `C:\Users\user\Desktop\alternate`.

### Files Modified/Created:
- `interactive_demo.py`: Completely rewritten to use `psycopg2` instead of `sqlite3`. Replaced all `?` placeholders with `%s` and updated the schema definition to PostgreSQL syntax. Injected 4 new DA2-specific menu options.
- `DA2_Implementation_Report.md` (This file): Added to serve as your final submission/testing guide.
- The original SQLite database (`campus_placement.db`) in this folder is now obsolete as data is stored in the Postgres server.

---

## 2. Setup Instructions

To run this new Postgres-backed version on your local machine, follow these steps:

### A. Install PostgreSQL
1. Download and install PostgreSQL from the official website.
2. During installation, remember the password you set for the default `postgres` user.
3. Open **pgAdmin 4** (installed alongside Postgres) or `psql`.
4. Create a new database named `campus_placement`.

### B. Install Python Dependencies
Open your terminal in the `alternate` folder and install the Postgres adapter:
```bash
pip install psycopg2
```
*(Note: If you get build errors on Windows, run `pip install psycopg2-binary` instead).*

### C. Configure Connection (Optional)
The script defaults to connecting to a database named `campus_placement` on `localhost` with the user `postgres` and password `postgres`.
If your password is different, set it via environment variables before running the script:
**PowerShell:**
```powershell
$env:PG_PASSWORD="your_actual_password"
```

---

## 3. How to Run the App
Navigate to your alternate folder and run the interactive demo:
```bash
cd C:\Users\user\Desktop\alternate
python interactive_demo.py
```
Upon the first run, the script will automatically detect an empty schema, create all tables (including the new Triggers, RLS policies, Indexes, and Stored Procedures), and seed the sample data.

---

## 4. How to Test DA2 Features

I have added dedicated options in the new Main Menu to test every DA2 requirement effortlessly.

### DA2 Requirement 1: Advanced Analytical Reporting (CUBE/ROLLUP)
* **Test it:** Select **Option 1** from the Main Menu.
* **What happens:** The backend queries the `mv_placement_stats` materialized view.
* **Under the hood:** The materialized view was generated using a `GROUP BY CUBE (d.dept_name, c.co_name)` query, which simultaneously breaks down offers by company, by department, and by overall totals.

### DA2 Requirement 2: PL/pgSQL Stored Procedure & Triggers
* **Test it:** Select **Option 2** from the Main Menu. Enter an App ID (`APP099`), Roll No (`25BCE1001`), and Job ID (`JOB002`).
* **What happens:** 
  1. The DB engine executes `CALL sp_apply_for_job(...)`. 
  2. The stored procedure locks the rows (`FOR SHARE`), checks eligibility, and inserts the application.
  3. The insertion fires the `trg_application_status` Trigger.
  4. The trigger logs the change into the `application_audit_logs` table.

### DA2 Requirement 3: Database-Level Security (Row-Level Security - RLS)
* **Test it:** Select **Option 3** from the Main Menu.
* **What happens:** The script dynamically changes the database session context (`SET app.current_role = 'student'; SET app.current_student = '25BCE5227';`). 
* **Under the hood:** Due to the RLS policy we created (`CREATE POLICY student_own_policy...`), when the student queries `SELECT * FROM applications;`, the database engine automatically blocks them from seeing any other student's applications. 

### DA2 Requirement 4: Performance Tuning (B+ Tree Indexes)
* **What happened:** We injected `CREATE INDEX idx_students_dept_cgpa ON students USING btree (dept_id, cgpa);` and an index on `job_postings`.
* **How to verify latency (For your professor):** 
  1. Open pgAdmin 4. 
  2. Run `EXPLAIN ANALYZE SELECT * FROM students WHERE dept_id = 'DEP001' AND cgpa >= 8.5;`.
  3. The output will show an **Index Scan** instead of a **Seq Scan**, mathematically proving execution optimization.
