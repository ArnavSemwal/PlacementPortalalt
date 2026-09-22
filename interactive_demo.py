import psycopg2
import psycopg2.extras
import os
import sys

# Default PostgreSQL Connection Parameters
PG_DB = os.environ.get("PG_DB", "campus_placement")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "2007")
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5432")

TABLES = [
    "departments",
    "addresses",
    "companies",
    "skills",
    "staff",
    "students",
    "resumes",
    "recruiters",
    "job_postings",
    "student_skills",
    "job_skills",
    "notifications",
    "applications",
    "application_audit_logs",
    "interviews",
    "offers",
]

def print_banner(title: str):
    width = 88
    print("\n" + "=" * width)
    print(f" {title.center(width - 2)} ")
    print("=" * width)

def print_section(title: str):
    width = 88
    print("\n" + "-" * width)
    print(f"  [+] {title}")
    print("-" * width)

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        conn.cursor_factory = psycopg2.extras.DictCursor
        return conn
    except psycopg2.Error as e:
        print(f"  [FATAL] Could not connect to PostgreSQL: {e}")
        print("  Please ensure PostgreSQL is running and credentials are correct.")
        sys.exit(1)

def initialize_database(conn):
    cur = conn.cursor()
    print("  [INFO] Initializing PostgreSQL Schema...")

    for table in reversed(TABLES):
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS mv_placement_stats CASCADE;")
    cur.execute("DROP FUNCTION IF EXISTS log_application_status_change CASCADE;")
    cur.execute("DROP PROCEDURE IF EXISTS sp_apply_for_job CASCADE;")

    cur.execute("""
        CREATE TABLE departments (
            dept_id TEXT PRIMARY KEY,
            dept_name TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE addresses (
            address_id TEXT PRIMARY KEY,
            city TEXT NOT NULL,
            state TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE companies (
            co_id TEXT PRIMARY KEY,
            co_name TEXT NOT NULL UNIQUE,
            industry TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE skills (
            skill_id TEXT PRIMARY KEY,
            skill_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL CHECK (category IN ('Programming', 'Database', 'Cloud', 'Networking', 'AI/ML', 'Hardware', 'Soft Skills'))
        );
    """)

    cur.execute("""
        CREATE TABLE staff (
            staff_id TEXT PRIMARY KEY,
            staff_name TEXT NOT NULL,
            designation TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE students (
            roll_no TEXT PRIMARY KEY,
            dept_id TEXT NOT NULL REFERENCES departments(dept_id),
            address_id TEXT NOT NULL REFERENCES addresses(address_id),
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            cgpa REAL NOT NULL CHECK (cgpa >= 0.00 AND cgpa <= 10.00)
        );
    """)

    cur.execute("""
        CREATE TABLE resumes (
            resume_id TEXT PRIMARY KEY,
            roll_no TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
            file_url TEXT NOT NULL,
            upload_date TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE recruiters (
            recruiter_id TEXT PRIMARY KEY,
            co_id TEXT NOT NULL REFERENCES companies(co_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE job_postings (
            job_id TEXT PRIMARY KEY,
            co_id TEXT NOT NULL REFERENCES companies(co_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            package_lpa REAL NOT NULL CHECK (package_lpa > 0.00),
            min_cgpa REAL NOT NULL CHECK (min_cgpa >= 0.00 AND min_cgpa <= 10.00)
        );
    """)

    cur.execute("""
        CREATE TABLE student_skills (
            roll_no TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
            skill_id TEXT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
            PRIMARY KEY (roll_no, skill_id)
        );
    """)

    cur.execute("""
        CREATE TABLE job_skills (
            job_id TEXT NOT NULL REFERENCES job_postings(job_id) ON DELETE CASCADE,
            skill_id TEXT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
            PRIMARY KEY (job_id, skill_id)
        );
    """)

    cur.execute("""
        CREATE TABLE notifications (
            notif_id TEXT PRIMARY KEY,
            staff_id TEXT NOT NULL REFERENCES staff(staff_id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            sent_date TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE applications (
            app_id TEXT PRIMARY KEY,
            roll_no TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
            job_id TEXT NOT NULL REFERENCES job_postings(job_id) ON DELETE CASCADE,
            staff_id TEXT NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
            status TEXT NOT NULL CHECK (status IN ('Pending', 'Shortlisted', 'Interviewing', 'Rejected', 'Hired')),
            UNIQUE (roll_no, job_id)
        );
    """)

    cur.execute("""
        CREATE TABLE interviews (
            interview_id TEXT PRIMARY KEY,
            app_id TEXT NOT NULL REFERENCES applications(app_id) ON DELETE CASCADE,
            recruiter_id TEXT NOT NULL REFERENCES recruiters(recruiter_id) ON DELETE RESTRICT,
            mode TEXT NOT NULL CHECK (mode IN ('Online', 'In-Person', 'Hybrid')),
            result TEXT NOT NULL CHECK (result IN ('Pending', 'Cleared', 'Failed'))
        );
    """)

    cur.execute("""
        CREATE TABLE offers (
            offer_id TEXT PRIMARY KEY,
            app_id TEXT NOT NULL UNIQUE REFERENCES applications(app_id) ON DELETE CASCADE,
            package_offered REAL NOT NULL CHECK (package_offered > 0.00),
            offer_status TEXT NOT NULL CHECK (offer_status IN ('Offered', 'Accepted', 'Declined', 'Revoked'))
        );
    """)

    # --- ENTERPRISE: B-TREE INDEXES ---
    print("  [INFO] Creating B-Tree Composite Indexes...")
    cur.execute("CREATE INDEX idx_students_dept_cgpa ON students USING btree (dept_id, cgpa);")
    cur.execute("CREATE INDEX idx_job_postings_min_cgpa ON job_postings USING btree (min_cgpa);")

    # --- ENTERPRISE: AUDIT TABLE ---
    print("  [INFO] Setting up Audit Logs Table...")
    cur.execute("""
        CREATE TABLE application_audit_logs (
            log_id SERIAL PRIMARY KEY,
            app_id TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- ENTERPRISE: TRIGGER FUNCTION ---
    print("  [INFO] Creating Trigger Function...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION log_application_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) OR TG_OP = 'INSERT' THEN
                INSERT INTO application_audit_logs (app_id, old_status, new_status)
                VALUES (
                    NEW.app_id,
                    CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.status END,
                    NEW.status
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute("""
        CREATE TRIGGER trg_application_status
        AFTER INSERT OR UPDATE ON applications
        FOR EACH ROW
        EXECUTE FUNCTION log_application_status_change();
    """)

    # --- ENTERPRISE: ROW-LEVEL SECURITY ---
    print("  [INFO] Enforcing Row-Level Security on Applications...")
    cur.execute("ALTER TABLE applications ENABLE ROW LEVEL SECURITY;")

    # Staff sees everything
    cur.execute("""
        CREATE POLICY admin_all_policy ON applications
        FOR ALL
        USING (current_setting('app.current_role', true) = 'staff');
    """)

    # Student sees only their own rows
    cur.execute("""
        CREATE POLICY student_own_policy ON applications
        FOR SELECT
        USING (
            current_setting('app.current_role', true) = 'student'
            AND roll_no = current_setting('app.current_student', true)
        );
    """)

    cur.execute("ALTER TABLE applications FORCE ROW LEVEL SECURITY;")

    # --- ENTERPRISE: STORED PROCEDURE ---
    # NOTE: The stored procedure does NOT contain COMMIT internally.
    # Commit is managed by the caller (psycopg2 with autocommit=True).
    print("  [INFO] Compiling sp_apply_for_job Stored Procedure...")
    cur.execute("""
        CREATE OR REPLACE PROCEDURE sp_apply_for_job(
            p_app_id TEXT,
            p_roll_no TEXT,
            p_job_id TEXT,
            p_staff_id TEXT
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_student_cgpa REAL;
            v_job_min_cgpa REAL;
        BEGIN
            -- Lock rows to prevent race conditions
            SELECT cgpa INTO v_student_cgpa
                FROM students WHERE roll_no = p_roll_no FOR SHARE;

            SELECT min_cgpa INTO v_job_min_cgpa
                FROM job_postings WHERE job_id = p_job_id FOR SHARE;

            -- Validate CGPA eligibility
            IF v_student_cgpa IS NULL THEN
                RAISE EXCEPTION 'Student with roll_no % not found.', p_roll_no;
            END IF;

            IF v_job_min_cgpa IS NULL THEN
                RAISE EXCEPTION 'Job with job_id % not found.', p_job_id;
            END IF;

            IF v_student_cgpa < v_job_min_cgpa THEN
                RAISE EXCEPTION 'Eligibility Failed: Student CGPA (%.2f) < Job Min CGPA (%.2f)',
                    v_student_cgpa, v_job_min_cgpa;
            END IF;

            -- Insert the application (triggers audit log automatically)
            INSERT INTO applications (app_id, roll_no, job_id, staff_id, status)
            VALUES (p_app_id, p_roll_no, p_job_id, p_staff_id, 'Pending');
        END;
        $$;
    """)

    # --- ENTERPRISE: MATERIALIZED VIEW (backed by CUBE) ---
    print("  [INFO] Creating Materialized View for Analytics...")
    cur.execute("""
        CREATE MATERIALIZED VIEW mv_placement_stats AS
        SELECT
            d.dept_name,
            c.co_name,
            COUNT(o.offer_id)                         AS total_offers,
            ROUND(AVG(o.package_offered)::numeric, 2) AS avg_package
        FROM offers o
        JOIN applications a ON o.app_id = a.app_id
        JOIN students s     ON a.roll_no = s.roll_no
        JOIN departments d  ON s.dept_id = d.dept_id
        JOIN job_postings j ON a.job_id = j.job_id
        JOIN companies c    ON j.co_id = c.co_id
        WHERE o.offer_status = 'Accepted'
        GROUP BY CUBE (d.dept_name, c.co_name)
        WITH NO DATA;
    """)

    conn.commit()
    print("  [SUCCESS] Schema initialized.")


def table_has_rows(conn, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cur.fetchone()[0] > 0


def seed_data(conn):
    cur = conn.cursor()

    if table_has_rows(conn, "departments"):
        print("  [INFO] Data already seeded, skipping.")
        return

    def insert_many(query, data):
        psycopg2.extras.execute_values(cur, query, data)

    # ── DEPARTMENTS (6) ──────────────────────────────────────────────────
    insert_many("INSERT INTO departments VALUES %s;", [
        ("DEP001", "Computer Science & Engineering",          "+91-44-2250-0101"),
        ("DEP002", "Information Technology",                  "+91-44-2250-0102"),
        ("DEP003", "Artificial Intelligence & Data Science",  "+91-44-2250-0103"),
        ("DEP004", "Electronics & Communication Engineering", "+91-44-2250-0104"),
        ("DEP005", "Mechanical Engineering",                  "+91-44-2250-0105"),
        ("DEP006", "Electrical & Electronics Engineering",    "+91-44-2250-0106"),
    ])

    # ── ADDRESSES (8) ────────────────────────────────────────────────────
    insert_many("INSERT INTO addresses VALUES %s;", [
        ("ADDR001", "Bengaluru",  "Karnataka"),
        ("ADDR002", "Chennai",    "Tamil Nadu"),
        ("ADDR003", "Hyderabad",  "Telangana"),
        ("ADDR004", "Pune",       "Maharashtra"),
        ("ADDR005", "Mumbai",     "Maharashtra"),
        ("ADDR006", "New Delhi",  "Delhi"),
        ("ADDR007", "Kolkata",    "West Bengal"),
        ("ADDR008", "Ahmedabad",  "Gujarat"),
    ])

    # ── COMPANIES (8) — Tech, Finance, Consulting, Core ──────────────────
    insert_many("INSERT INTO companies VALUES %s;", [
        ("CO001", "Google India",              "Information Technology & Cloud"),
        ("CO002", "Microsoft Corporation",     "Software & Enterprise Cloud"),
        ("CO003", "Goldman Sachs India",       "Investment Banking & Finance"),
        ("CO004", "McKinsey & Company",        "Management Consulting"),
        ("CO005", "Cisco Systems India",       "Networking & Telecommunications"),
        ("CO006", "Qualcomm India",            "Semiconductors & Embedded Systems"),
        ("CO007", "Tata Consultancy Services", "IT Services & Consulting"),
        ("CO008", "ABB India",                 "Power & Automation Engineering"),
    ])

    # ── SKILLS (15) ──────────────────────────────────────────────────────
    insert_many("INSERT INTO skills VALUES %s;", [
        ("SK001", "Python Programming",                  "Programming"),
        ("SK002", "Java Enterprise",                     "Programming"),
        ("SK003", "C++ System Architecture",             "Programming"),
        ("SK004", "Relational Database Design & SQL",    "Database"),
        ("SK005", "Oracle PL/SQL & Stored Logic",        "Database"),
        ("SK006", "Cloud Architecture (AWS/GCP)",        "Cloud"),
        ("SK007", "Distributed Systems & Microservices", "Cloud"),
        ("SK008", "Machine Learning & Deep Neural Nets", "AI/ML"),
        ("SK009", "Data Structures & Algorithms",        "Programming"),
        ("SK010", "Computer Networks & TCP/IP",          "Networking"),
        ("SK011", "Embedded C & RTOS",                   "Hardware"),
        ("SK012", "System Verilog & VLSI Design",        "Hardware"),
        ("SK013", "DevOps & Docker Containers",          "Cloud"),
        ("SK014", "Technical Communication",             "Soft Skills"),
        ("SK015", "Leadership & Team Management",        "Soft Skills"),
    ])

    # ── STAFF (4) ────────────────────────────────────────────────────────
    insert_many("INSERT INTO staff VALUES %s;", [
        ("STF001", "Dr. Sundararajan V.",  "Director - Training & Placement"),
        ("STF002", "Prof. Kavitha Raman",  "Senior Placement Officer - Tier 1 Firms"),
        ("STF003", "Mr. Dinesh Kumar",     "Placement Executive - Core Engineering"),
        ("STF004", "Ms. Shalini Murugan",  "T&P Compliance & Corporate Liaison"),
    ])

    # ── STUDENTS (20) — spread across depts, CGPAs 6.5 → 9.8 ─────────────
    insert_many("INSERT INTO students VALUES %s;", [
        # CSE — DEP001
        ("25BCE5227", "DEP001", "ADDR001", "Shashwat Siddhant",  "shashwat.siddhant@campus.edu",   9.80),
        ("25BCE5392", "DEP001", "ADDR002", "Arnav Semwal",        "arnav.semwal@campus.edu",         9.40),
        ("25BCE1001", "DEP001", "ADDR003", "Ananya Iyer",         "ananya.iyer@campus.edu",          9.10),
        ("25BCE1010", "DEP001", "ADDR004", "Kabir Das",           "kabir.das@campus.edu",            8.75),
        ("25BCE2021", "DEP001", "ADDR005", "Divya Nair",          "divya.nair@campus.edu",           8.20),
        # IT — DEP002
        ("25BIT2015", "DEP002", "ADDR006", "Neha Kulkarni",       "neha.kulkarni@campus.edu",        9.25),
        ("25BIT2002", "DEP002", "ADDR001", "Rohan Gupta",         "rohan.gupta@campus.edu",          8.60),
        ("25BIT2033", "DEP002", "ADDR007", "Sanya Mehta",         "sanya.mehta@campus.edu",          7.90),
        ("25BIT2044", "DEP002", "ADDR002", "Yash Agarwal",        "yash.agarwal@campus.edu",         7.40),
        # AI & DS — DEP003
        ("25BAI3003", "DEP003", "ADDR003", "Priya Sharma",        "priya.sharma@campus.edu",         9.60),
        ("25BAI3017", "DEP003", "ADDR008", "Karthik Menon",       "karthik.menon@campus.edu",        9.00),
        ("25BAI3029", "DEP003", "ADDR001", "Riya Desai",          "riya.desai@campus.edu",           8.40),
        # ECE — DEP004
        ("25BEC4004", "DEP004", "ADDR006", "Vikram Patel",        "vikram.patel@campus.edu",         8.00),
        ("25BEC4019", "DEP004", "ADDR004", "Aishwarya Krishnan",  "aishwarya.krishnan@campus.edu",   7.60),
        ("25BEC4031", "DEP004", "ADDR007", "Surya Narayan",       "surya.narayan@campus.edu",        7.10),
        # Mechanical — DEP005
        ("25BME5005", "DEP005", "ADDR004", "Aditya Verma",        "aditya.verma@campus.edu",         7.80),
        ("25BME5018", "DEP005", "ADDR005", "Pallavi Joshi",       "pallavi.joshi@campus.edu",        7.20),
        ("25BME5027", "DEP005", "ADDR008", "Tanmay Rao",          "tanmay.rao@campus.edu",           6.70),
        # EEE — DEP006
        ("25BEE6006", "DEP006", "ADDR003", "Meera Reddy",         "meera.reddy@campus.edu",          8.30),
        ("25BEE6021", "DEP006", "ADDR002", "Nikhil Bhat",         "nikhil.bhat@campus.edu",          6.50),
    ])

    # ── RESUMES (20) ─────────────────────────────────────────────────────
    resumes = [
        ("25BCE5227", "shashwat_v3"),  ("25BCE5392", "arnav_v2"),
        ("25BCE1001", "ananya_v1"),    ("25BCE1010", "kabir_v1"),
        ("25BCE2021", "divya_v1"),     ("25BIT2015", "neha_v2"),
        ("25BIT2002", "rohan_v1"),     ("25BIT2033", "sanya_v1"),
        ("25BIT2044", "yash_v1"),      ("25BAI3003", "priya_v2"),
        ("25BAI3017", "karthik_v1"),   ("25BAI3029", "riya_v1"),
        ("25BEC4004", "vikram_v1"),    ("25BEC4019", "aishwarya_v1"),
        ("25BEC4031", "surya_v1"),     ("25BME5005", "aditya_v1"),
        ("25BME5018", "pallavi_v1"),   ("25BME5027", "tanmay_v1"),
        ("25BEE6006", "meera_v1"),     ("25BEE6021", "nikhil_v1"),
    ]
    insert_many("INSERT INTO resumes VALUES %s;", [
        (f"RES{str(i+1).zfill(3)}", roll, f"https://storage.campus.edu/cv/{slug}.pdf", "2026-08-01")
        for i, (roll, slug) in enumerate(resumes)
    ])

    # ── RECRUITERS (8) ───────────────────────────────────────────────────
    insert_many("INSERT INTO recruiters VALUES %s;", [
        ("REC001", "CO001", "Aravind Swaminathan", "+91-80-6721-5001"),
        ("REC002", "CO002", "Deepa Krishnan",      "+91-80-4000-6002"),
        ("REC003", "CO003", "Raghav Malhotra",     "+91-22-6631-4000"),
        ("REC004", "CO004", "Sneha Pillai",         "+91-22-7100-5500"),
        ("REC005", "CO005", "Rajeev Menon",         "+91-80-4422-9005"),
        ("REC006", "CO006", "Karthik Balan",        "+91-80-4112-3456"),
        ("REC007", "CO007", "Sunita Rao",           "+91-22-6778-1001"),
        ("REC008", "CO008", "Sandeep Verma",        "+91-11-2343-8800"),
    ])

    # ── JOB POSTINGS (10) — package 6 → 54 LPA ───────────────────────────
    insert_many("INSERT INTO job_postings VALUES %s;", [
        ("JOB001", "CO001", "Software Development Engineer - II",       54.00, 9.00),
        ("JOB002", "CO002", "Cloud & AI Platform Engineer",             46.00, 8.75),
        ("JOB003", "CO003", "Technology Analyst - Quant Finance",       42.00, 8.50),
        ("JOB004", "CO004", "Junior Management Consultant",             38.00, 8.50),
        ("JOB005", "CO001", "ML Research Engineer (Applied AI)",        50.00, 9.25),
        ("JOB006", "CO005", "Network Systems Engineer",                 24.00, 7.50),
        ("JOB007", "CO006", "Embedded Firmware Engineer",               26.00, 7.00),
        ("JOB008", "CO007", "Digital Transformation Analyst",           12.00, 6.50),
        ("JOB009", "CO008", "Electrical Design Engineer",               14.00, 6.50),
        ("JOB010", "CO002", "Developer Advocate & Cloud Evangelist",    32.00, 7.75),
    ])

    # ── STUDENT SKILLS ────────────────────────────────────────────────────
    insert_many("INSERT INTO student_skills VALUES %s;", [
        # CSE
        ("25BCE5227", "SK001"), ("25BCE5227", "SK004"), ("25BCE5227", "SK007"),
        ("25BCE5227", "SK009"), ("25BCE5227", "SK006"),
        ("25BCE5392", "SK002"), ("25BCE5392", "SK004"), ("25BCE5392", "SK009"),
        ("25BCE5392", "SK013"), ("25BCE5392", "SK007"),
        ("25BCE1001", "SK001"), ("25BCE1001", "SK002"), ("25BCE1001", "SK009"),
        ("25BCE1001", "SK004"),
        ("25BCE1010", "SK001"), ("25BCE1010", "SK009"), ("25BCE1010", "SK014"),
        ("25BCE2021", "SK001"), ("25BCE2021", "SK009"), ("25BCE2021", "SK014"),
        # IT
        ("25BIT2015", "SK002"), ("25BIT2015", "SK004"), ("25BIT2015", "SK013"),
        ("25BIT2015", "SK006"),
        ("25BIT2002", "SK001"), ("25BIT2002", "SK004"), ("25BIT2002", "SK009"),
        ("25BIT2033", "SK002"), ("25BIT2033", "SK014"), ("25BIT2033", "SK010"),
        ("25BIT2044", "SK001"), ("25BIT2044", "SK014"),
        # AI & DS
        ("25BAI3003", "SK001"), ("25BAI3003", "SK008"), ("25BAI3003", "SK006"),
        ("25BAI3003", "SK009"), ("25BAI3003", "SK004"),
        ("25BAI3017", "SK001"), ("25BAI3017", "SK008"), ("25BAI3017", "SK009"),
        ("25BAI3029", "SK001"), ("25BAI3029", "SK008"),
        # ECE
        ("25BEC4004", "SK003"), ("25BEC4004", "SK011"), ("25BEC4004", "SK012"),
        ("25BEC4019", "SK011"), ("25BEC4019", "SK010"),
        ("25BEC4031", "SK011"), ("25BEC4031", "SK014"),
        # Mechanical
        ("25BME5005", "SK014"), ("25BME5005", "SK015"),
        ("25BME5018", "SK015"), ("25BME5018", "SK014"),
        ("25BME5027", "SK014"),
        # EEE
        ("25BEE6006", "SK010"), ("25BEE6006", "SK011"), ("25BEE6006", "SK014"),
        ("25BEE6021", "SK014"), ("25BEE6021", "SK015"),
    ])

    # ── JOB SKILLS ────────────────────────────────────────────────────────
    insert_many("INSERT INTO job_skills VALUES %s;", [
        ("JOB001", "SK001"), ("JOB001", "SK007"), ("JOB001", "SK009"),
        ("JOB002", "SK001"), ("JOB002", "SK006"), ("JOB002", "SK013"),
        ("JOB003", "SK004"), ("JOB003", "SK009"), ("JOB003", "SK001"),
        ("JOB004", "SK014"), ("JOB004", "SK015"), ("JOB004", "SK009"),
        ("JOB005", "SK001"), ("JOB005", "SK008"), ("JOB005", "SK009"),
        ("JOB006", "SK003"), ("JOB006", "SK010"),
        ("JOB007", "SK003"), ("JOB007", "SK011"), ("JOB007", "SK012"),
        ("JOB008", "SK001"), ("JOB008", "SK004"), ("JOB008", "SK014"),
        ("JOB009", "SK011"), ("JOB009", "SK012"),
        ("JOB010", "SK006"), ("JOB010", "SK013"), ("JOB010", "SK014"),
    ])

    # ── NOTIFICATIONS (5) ─────────────────────────────────────────────────
    insert_many("INSERT INTO notifications VALUES %s;", [
        ("NOT001", "STF001", "Campus Placement Drive 2026-27 is officially OPEN.", "2026-08-01 09:00:00"),
        ("NOT002", "STF002", "Google India applications close on 20-Aug-2026.",      "2026-08-05 14:30:00"),
        ("NOT003", "STF002", "Microsoft & Goldman Sachs GDs scheduled for 25-Aug.",  "2026-08-10 11:00:00"),
        ("NOT004", "STF003", "McKinsey case-study round results announced.",          "2026-09-01 10:00:00"),
        ("NOT005", "STF004", "Final offer letters to be collected from T&P office.",  "2026-09-10 09:00:00"),
    ])

    # ── APPLICATIONS (30) — set staff role so RLS permits the inserts ──────
    cur.execute("""SET "app.current_role" = 'staff';""")
    insert_many("INSERT INTO applications VALUES %s;", [
        # Google JOB001 (cutoff 9.0)
        ("APP001", "25BCE5227", "JOB001", "STF002", "Hired"),
        ("APP002", "25BAI3003", "JOB001", "STF002", "Hired"),
        ("APP003", "25BCE5392", "JOB001", "STF002", "Rejected"),
        ("APP004", "25BCE1001", "JOB001", "STF002", "Shortlisted"),
        # Google JOB005 ML (cutoff 9.25)
        ("APP005", "25BCE5227", "JOB005", "STF002", "Hired"),
        ("APP006", "25BAI3003", "JOB005", "STF002", "Shortlisted"),
        ("APP007", "25BAI3017", "JOB005", "STF002", "Rejected"),
        # Microsoft JOB002 (cutoff 8.75)
        ("APP008", "25BCE5392", "JOB002", "STF002", "Hired"),
        ("APP009", "25BIT2015", "JOB002", "STF002", "Hired"),
        ("APP010", "25BCE1001", "JOB002", "STF002", "Interviewing"),
        ("APP011", "25BAI3003", "JOB002", "STF002", "Shortlisted"),
        # Goldman Sachs JOB003 (cutoff 8.5)
        ("APP012", "25BCE5392", "JOB003", "STF002", "Hired"),
        ("APP013", "25BCE1010", "JOB003", "STF002", "Rejected"),
        ("APP014", "25BIT2015", "JOB003", "STF002", "Shortlisted"),
        ("APP015", "25BAI3003", "JOB003", "STF002", "Pending"),
        # McKinsey JOB004 (cutoff 8.5)
        ("APP016", "25BCE5227", "JOB004", "STF001", "Hired"),
        ("APP017", "25BCE5392", "JOB004", "STF001", "Rejected"),
        ("APP018", "25BIT2015", "JOB004", "STF001", "Shortlisted"),
        ("APP019", "25BAI3017", "JOB004", "STF001", "Pending"),
        # Microsoft Developer Advocate JOB010 (cutoff 7.75)
        ("APP020", "25BIT2002", "JOB010", "STF002", "Hired"),
        ("APP021", "25BIT2033", "JOB010", "STF002", "Interviewing"),
        ("APP022", "25BCE2021", "JOB010", "STF002", "Pending"),
        # Cisco JOB006 (cutoff 7.5)
        ("APP023", "25BEC4004", "JOB006", "STF003", "Hired"),
        ("APP024", "25BEE6006", "JOB006", "STF003", "Shortlisted"),
        ("APP025", "25BIT2033", "JOB006", "STF003", "Rejected"),
        # Qualcomm JOB007 (cutoff 7.0)
        ("APP026", "25BEC4004", "JOB007", "STF003", "Hired"),
        ("APP027", "25BEC4019", "JOB007", "STF003", "Interviewing"),
        ("APP028", "25BEC4031", "JOB007", "STF003", "Pending"),
        # TCS JOB008 (cutoff 6.5)
        ("APP029", "25BME5005", "JOB008", "STF004", "Hired"),
        ("APP030", "25BME5018", "JOB008", "STF004", "Hired"),
        # ABB JOB009 (cutoff 6.5)
        ("APP031", "25BEE6006", "JOB009", "STF004", "Hired"),
        ("APP032", "25BEE6021", "JOB009", "STF004", "Interviewing"),
        ("APP033", "25BME5027", "JOB009", "STF004", "Pending"),
        # TCS — IT students
        ("APP034", "25BIT2044", "JOB008", "STF004", "Hired"),
        ("APP035", "25BCE1010", "JOB008", "STF004", "Shortlisted"),
    ])

    # ── INTERVIEWS (for Hired, Cleared, and Pending apps) ─────────────────
    insert_many("INSERT INTO interviews VALUES %s;", [
        ("INT001", "APP001", "REC001", "Online",    "Cleared"),
        ("INT002", "APP002", "REC001", "Online",    "Cleared"),
        ("INT003", "APP003", "REC001", "In-Person", "Failed"),
        ("INT004", "APP005", "REC001", "Online",    "Cleared"),
        ("INT005", "APP008", "REC002", "Online",    "Cleared"),
        ("INT006", "APP009", "REC002", "Online",    "Cleared"),
        ("INT007", "APP010", "REC002", "Hybrid",    "Pending"),
        ("INT008", "APP012", "REC003", "In-Person", "Cleared"),
        ("INT009", "APP013", "REC003", "In-Person", "Failed"),
        ("INT010", "APP016", "REC004", "In-Person", "Cleared"),
        ("INT011", "APP017", "REC004", "In-Person", "Failed"),
        ("INT012", "APP020", "REC002", "Online",    "Cleared"),
        ("INT013", "APP021", "REC002", "Online",    "Pending"),
        ("INT014", "APP023", "REC005", "Online",    "Cleared"),
        ("INT015", "APP026", "REC006", "In-Person", "Cleared"),
        ("INT016", "APP027", "REC006", "In-Person", "Pending"),
        ("INT017", "APP029", "REC007", "Online",    "Cleared"),
        ("INT018", "APP030", "REC007", "Online",    "Cleared"),
        ("INT019", "APP031", "REC008", "Online",    "Cleared"),
        ("INT020", "APP034", "REC007", "Online",    "Cleared"),
    ])

    # ── OFFERS (for all Hired applications) ───────────────────────────────
    insert_many("INSERT INTO offers VALUES %s;", [
        ("OFR001", "APP001", 54.00, "Accepted"),   # Shashwat — Google SDE-II
        ("OFR002", "APP002", 54.00, "Accepted"),   # Priya — Google SDE-II
        ("OFR003", "APP005", 50.00, "Accepted"),   # Shashwat — Google ML
        ("OFR004", "APP008", 46.00, "Accepted"),   # Arnav — Microsoft Cloud
        ("OFR005", "APP009", 46.00, "Accepted"),   # Neha — Microsoft Cloud
        ("OFR006", "APP012", 42.00, "Accepted"),   # Arnav — Goldman Sachs
        ("OFR007", "APP016", 38.00, "Accepted"),   # Shashwat — McKinsey
        ("OFR008", "APP020", 32.00, "Accepted"),   # Rohan — MS DevAdvocate
        ("OFR009", "APP023", 24.00, "Accepted"),   # Vikram — Cisco
        ("OFR010", "APP026", 26.00, "Accepted"),   # Vikram — Qualcomm
        ("OFR011", "APP029", 12.00, "Accepted"),   # Aditya — TCS
        ("OFR012", "APP030", 12.00, "Accepted"),   # Pallavi — TCS
        ("OFR013", "APP031", 14.00, "Accepted"),   # Meera — ABB
        ("OFR014", "APP034", 12.00, "Accepted"),   # Yash — TCS
    ])

    # ── POPULATE MATERIALIZED VIEW ─────────────────────────────────────────
    cur.execute("REFRESH MATERIALIZED VIEW mv_placement_stats;")

    conn.commit()
    print("  [SUCCESS] Rich dataset loaded: 20 students, 35 applications, 14 offers, M-View refreshed.")


def print_query_result(title: str, cur):
    rows = cur.fetchall()
    if not rows:
        print(f"\n  {title}: (No rows found)")
        return

    columns = [desc[0] for desc in cur.description]
    widths = [len(str(c)) for c in columns]
    formatted_rows = [[str(v) if v is not None else 'NULL' for v in row] for row in rows]
    for row in formatted_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    print(f"\n  {title}")
    print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(columns)))
    print("  " + "-+-".join("-" * widths[i] for i in range(len(columns))))
    for row in formatted_rows:
        print("  " + " | ".join(val.ljust(widths[i]) for i, val in enumerate(row)))


# ─────────────────────────────────────────────────────────
#  STANDARD CRUD OPERATIONS (Original Features Restored)
# ─────────────────────────────────────────────────────────

def show_tables(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
    )
    tables = [row[0] for row in cur.fetchall()]
    print_section("LIST OF TABLES")
    if not tables:
        print("  No tables found.")
        return
    for name in tables:
        print(f"  - {name}")


def describe_all_tables(conn):
    print_section("SCHEMA DESCRIPTION")
    for table in TABLES:
        cur = conn.cursor()
        cur.execute(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            f"WHERE table_schema = 'public' AND table_name = '{table}' "
            "ORDER BY ordinal_position;"
        )
        cols = cur.fetchall()
        print(f"\n  TABLE: {table}")
        if not cols:
            print("    (No columns found)")
            continue
        for col in cols:
            name, dtype, is_nullable, default_val = col
            notnull = is_nullable == "NO"
            print(f"    - {name}: {dtype} | NOT NULL={notnull} | DEFAULT={default_val}")


def view_selected_table(conn):
    print("  Available tables:")
    for t in TABLES:
        print(f"    - {t}")
    table_name = input("  Enter table name: ").strip()
    if table_name not in TABLES:
        print("  Invalid table name.")
        return

    cur = conn.cursor()
    cur.execute("""SET "app.current_role" = 'staff';""")
    cur.execute(f"SELECT * FROM {table_name} LIMIT 50;")
    print_query_result(f"DATA FROM {table_name}", cur)


def display_all_tables(conn):
    cur = conn.cursor()
    cur.execute("""SET "app.current_role" = 'staff';""")
    for table in TABLES:
        cur.execute(f"SELECT * FROM {table} LIMIT 20;")
        print_query_result(f"{table} (up to 20 shown)", cur)


def custom_query(conn):
    print_section("CUSTOM SQL QUERY")
    q = input("  Enter SQL statement: ").strip()
    if not q:
        print("  No SQL entered.")
        return

    try:
        cur = conn.cursor()
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(q)
        if cur.description:
            print_query_result("CUSTOM QUERY RESULT", cur)
        else:
            conn.commit()
            print("  Query executed successfully.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  SQL Error: {e}")


def get_table_columns(conn, table_name):
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = 'public' AND table_name = '{table_name}' "
        "ORDER BY ordinal_position;"
    )
    return [row[0] for row in cur.fetchall()]


def insert_record(conn):
    print_section("INSERT RECORD")
    print("  Available tables:")
    for t in TABLES:
        print(f"    - {t}")
    table_name = input("  Enter table name: ").strip()
    if table_name not in TABLES:
        print("  Invalid table name.")
        return

    columns = get_table_columns(conn, table_name)
    if not columns:
        print("  Table has no columns.")
        return

    values = []
    print(f"  Enter values for table '{table_name}'")
    for col in columns:
        value = input(f"    {col}: ").strip()
        if value == "" or value.lower() == "null":
            values.append(None)
        else:
            values.append(value)

    try:
        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)
        cur = conn.cursor()
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders});", values)
        conn.commit()
        print(f"  [SUCCESS] Record inserted into {table_name}.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  Insert failed: {e}")


def update_record(conn):
    print_section("UPDATE RECORD")
    print("  Available tables:")
    for t in TABLES:
        print(f"    - {t}")
    table_name = input("  Enter table name: ").strip()
    if table_name not in TABLES:
        print("  Invalid table name.")
        return

    columns = get_table_columns(conn, table_name)
    if not columns:
        print("  Table has no columns.")
        return

    cur = conn.cursor()
    cur.execute("""SET "app.current_role" = 'staff';""")
    cur.execute(f"SELECT * FROM {table_name} LIMIT 20;")
    rows = cur.fetchall()
    if rows:
        print_query_result(f"Current rows in {table_name}", cur)
    else:
        print("  No rows available to update.")
        return

    print("  Columns available:")
    for c in columns:
        print(f"    - {c}")

    filter_col = input("  Enter column to match: ").strip()
    if filter_col not in columns:
        print("  Invalid filter column.")
        return

    filter_val = input(f"  Enter value for {filter_col}: ").strip()
    update_col = input("  Enter column to update: ").strip()
    if update_col not in columns:
        print("  Invalid update column.")
        return

    new_value = input(f"  Enter new value for {update_col}: ").strip()
    if new_value == "":
        new_value = None

    try:
        cur = conn.cursor()
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(
            f"UPDATE {table_name} SET {update_col} = %s WHERE {filter_col} = %s;",
            (new_value, filter_val),
        )
        conn.commit()
        print(f"  [SUCCESS] Updated rows in {table_name}.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  Update failed: {e}")


def delete_record(conn):
    print_section("DELETE RECORD")
    print("  Available tables:")
    for t in TABLES:
        print(f"    - {t}")
    table_name = input("  Enter table name: ").strip()
    if table_name not in TABLES:
        print("  Invalid table name.")
        return

    columns = get_table_columns(conn, table_name)
    if not columns:
        print("  Table has no columns.")
        return

    cur = conn.cursor()
    cur.execute("""SET "app.current_role" = 'staff';""")
    cur.execute(f"SELECT * FROM {table_name} LIMIT 20;")
    print_query_result(f"Rows in {table_name}", cur)

    filter_col = input("  Enter column to match: ").strip()
    if filter_col not in columns:
        print("  Invalid column.")
        return

    filter_val = input(f"  Enter value for {filter_col}: ").strip()
    try:
        cur = conn.cursor()
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(
            f"DELETE FROM {table_name} WHERE {filter_col} = %s;",
            (filter_val,),
        )
        conn.commit()
        print(f"  [SUCCESS] Deleted matching record(s) from {table_name}.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  Delete failed: {e}")


def search_records(conn):
    print_section("SEARCH RECORDS")
    print("  Available tables:")
    for t in TABLES:
        print(f"    - {t}")
    table_name = input("  Enter table name: ").strip()
    if table_name not in TABLES:
        print("  Invalid table name.")
        return

    columns = get_table_columns(conn, table_name)
    if not columns:
        print("  Table has no columns.")
        return

    print("  Available columns:")
    for c in columns:
        print(f"    - {c}")

    filter_col = input("  Enter search column: ").strip()
    if filter_col not in columns:
        print("  Invalid search column.")
        return

    search_value = input(f"  Enter value to search for in {filter_col}: ").strip()
    try:
        cur = conn.cursor()
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(
            f"SELECT * FROM {table_name} WHERE CAST({filter_col} AS TEXT) ILIKE %s LIMIT 50;",
            (f"%{search_value}%",),
        )
        print_query_result(f"SEARCH RESULTS IN {table_name}", cur)
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  Search failed: {e}")


def reinitialize_database(conn):
    initialize_database(conn)
    seed_data(conn)
    print("  [SUCCESS] Database has been reset and reloaded.")


# ─────────────────────────────────────────────────────────
#  ENTERPRISE EDITION — ADVANCED FEATURES
# ─────────────────────────────────────────────────────────

def demo_analytical_query(conn):
    """
    Advanced Analytical Reporting using CUBE and ROLLUP.
    - Refreshes the Materialized View before reading it (fixes 'not populated' error).
    - Shows CUBE multi-dimensional results from the M-View.
    - Also runs a live ROLLUP query for department subtotals.
    """
    print_section("ADVANCED ANALYTICAL REPORTING (CUBE / ROLLUP)")
    cur = conn.cursor()

    # Step 1: Always refresh the materialized view so it is never empty.
    print("  Step 1: Refreshing Materialized View (mv_placement_stats)...")
    cur.execute("REFRESH MATERIALIZED VIEW mv_placement_stats;")
    conn.commit()
    print("  [OK] Materialized View refreshed successfully.")

    # Step 2: Read from the Materialized View (built using GROUP BY CUBE).
    print("\n  Step 2: Reading CUBE output from Materialized View...")
    cur.execute("""
        SELECT
            COALESCE(dept_name, 'ALL DEPARTMENTS') AS department,
            COALESCE(co_name,   'ALL COMPANIES')   AS company,
            COALESCE(total_offers, 0)              AS total_offers,
            COALESCE(avg_package,  0)              AS avg_package_lpa
        FROM mv_placement_stats
        ORDER BY dept_name NULLS LAST, co_name NULLS LAST;
    """)
    print_query_result(
        "CUBE Report: Placements by Dept x Company  (NULL rows = grand totals)", cur
    )

    # Step 3: Run a live ROLLUP query for department-level subtotals.
    print("\n  Step 3: Running live ROLLUP query (department subtotals)...")
    cur.execute("""
        SELECT
            COALESCE(d.dept_name, 'GRAND TOTAL')          AS department,
            COUNT(o.offer_id)                              AS total_placed,
            ROUND(AVG(o.package_offered)::numeric, 2)     AS avg_pkg_lpa,
            MAX(o.package_offered)                        AS max_pkg_lpa
        FROM offers o
        JOIN applications a ON o.app_id  = a.app_id
        JOIN students     s ON a.roll_no = s.roll_no
        JOIN departments  d ON s.dept_id = d.dept_id
        WHERE o.offer_status = 'Accepted'
        GROUP BY ROLLUP (d.dept_name)
        ORDER BY department NULLS LAST;
    """)
    print_query_result(
        "ROLLUP Report: Placements by Department (last row = grand total)", cur
    )


def demo_stored_procedure(conn):
    """
    Demonstrates the PL/pgSQL Stored Procedure and the Audit Trigger.

    Key fix: psycopg2 wraps everything in an implicit transaction by default.
    A stored procedure that contains its own transaction control (COMMIT) cannot
    run inside an outer transaction.  We temporarily switch the connection to
    autocommit mode, call the procedure, then restore normal mode.
    """
    print_section("ENTERPRISE: PL/pgSQL STORED PROCEDURE — sp_apply_for_job")
    print("  This procedure validates CGPA eligibility, inserts the application,")
    print("  and automatically fires the audit-log trigger.\n")

    # Show available students and jobs as a quick reference
    cur = conn.cursor()
    cur.execute("""SET "app.current_role" = 'staff';""")
    cur.execute("SELECT roll_no, name, cgpa FROM students ORDER BY cgpa DESC;")
    print_query_result("Available Students", cur)

    cur.execute("SELECT job_id, title, min_cgpa FROM job_postings ORDER BY min_cgpa DESC;")
    print_query_result("Available Jobs", cur)

    app_id  = input("\n  Enter New App ID   (e.g., APP099): ").strip()
    roll_no = input("  Enter Student Roll No (e.g., 25BCE1001): ").strip()
    job_id  = input("  Enter Job ID          (e.g., JOB002): ").strip()

    try:
        # Close any open implicit transaction before switching autocommit mode.
        # psycopg2 always starts a transaction immediately; set_session() (and
        # autocommit) raise ProgrammingError if called mid-transaction.
        conn.rollback()
        conn.autocommit = True

        cur = conn.cursor()
        # RLS must be set in the same session even in autocommit mode
        cur.execute("""SET "app.current_role" = 'staff';""")
        cur.execute(
            "CALL sp_apply_for_job(%s, %s, %s, 'STF001');",
            (app_id, roll_no, job_id),
        )
        print(f"\n  [SUCCESS] Application '{app_id}' inserted via Stored Procedure!")

        # Show the audit log entry that the trigger created
        cur.execute(
            "SELECT log_id, app_id, old_status, new_status, changed_at "
            "FROM application_audit_logs ORDER BY log_id DESC LIMIT 1;"
        )
        print_query_result("Audit Log Entry auto-generated by Trigger", cur)

    except psycopg2.Error as e:
        print(f"\n  [ERROR] {e.pgerror or e}")
    finally:
        # Always restore normal (non-autocommit) transaction behaviour
        conn.autocommit = False


def demo_rls(conn):
    """
    Demonstrates Row-Level Security by switching session contexts.

    How it works:
      - 'staff' role  → admin_all_policy  → sees ALL applications.
      - 'student' role → student_own_policy → sees ONLY their own application rows.
    The filtering is enforced by the PostgreSQL engine itself, not application code.
    """
    print_section("ENTERPRISE: ROW-LEVEL SECURITY (RLS) — Live Demonstration")

    cur = conn.cursor()

    # ── Context 1: Staff (should see every row) ──────────────────────────
    cur.execute("""SET "app.current_role" = 'staff';""")
    cur.execute("SELECT COUNT(*) FROM applications;")
    staff_count = cur.fetchone()[0]
    print(f"\n  [STAFF ROLE]   Total application rows visible : {staff_count}")

    cur.execute(
        "SELECT app_id, roll_no, job_id, status FROM applications ORDER BY app_id;"
    )
    print_query_result("ALL Applications visible to Staff (admin_all_policy)", cur)

    # ── Context 2: Student 25BCE5227 (should see only their own rows) ────
    test_roll = "25BCE5227"
    cur.execute("""SET "app.current_role" = 'student';""")
    cur.execute(f"""SET "app.current_student" = '{test_roll}';""")
    cur.execute("SELECT app_id, roll_no, job_id, status FROM applications;")
    print_query_result(
        f"Applications visible to Student {test_roll} — DB engine filters automatically",
        cur,
    )

    # ── Context 3: A different student with no applications ──────────────
    other_roll = "25BCE1010"
    cur.execute(f"""SET "app.current_student" = '{other_roll}';""")
    cur.execute("SELECT app_id, roll_no, job_id, status FROM applications;")
    print_query_result(
        f"Applications visible to Student {other_roll} — (expects fewer / no rows)",
        cur,
    )

    # Reset to staff so subsequent menu options don't break
    cur.execute("""SET "app.current_role" = 'staff';""")
    conn.commit()
    print("\n  [INFO] Session role reset to staff.")


# ─────────────────────────────────────────────────────────
#  MENU & MAIN
# ─────────────────────────────────────────────────────────

def show_menu():
    print_banner("CAMPUS PLACEMENT DATABASE MENU")
    print("  ─── Standard Operations ────────────────────────────────────")
    print("  1.  Display all tables")
    print("  2.  Describe all tables (schema)")
    print("  3.  View selected table values")
    print("  4.  Display ALL tables data")
    print("  5.  Run custom SQL query")
    print("  6.  Insert a record")
    print("  7.  Update a record")
    print("  8.  Delete a record")
    print("  9.  Search records")
    print("  10. Reinitialize database (reset + re-seed)")
    print("  ─── Enterprise Edition: Advanced Features ───────────────────")
    print("  11. CUBE / ROLLUP Analytical Reporting (+ refresh M-View)")
    print("  12. Apply for Job via Stored Procedure (shows Trigger log)")
    print("  13. Test Row-Level Security (RLS) enforcement")
    print("  ─────────────────────────────────────────────────────────────")
    print("  14. Exit")


def main():
    print_banner("THE CAMPUS PLACEMENT PORTAL — ENTERPRISE EDITION")
    print(f"  Database : {PG_DB}  |  Host: {PG_HOST}:{PG_PORT}  |  User: {PG_USER}")

    conn = get_connection()
    try:
        # Auto-initialize schema on first run
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.students');")
        if cur.fetchone()[0] is None:
            initialize_database(conn)
            seed_data(conn)

        while True:
            show_menu()
            choice = input("\n  Enter your choice: ").strip()

            if   choice == "1":  show_tables(conn)
            elif choice == "2":  describe_all_tables(conn)
            elif choice == "3":  view_selected_table(conn)
            elif choice == "4":  display_all_tables(conn)
            elif choice == "5":  custom_query(conn)
            elif choice == "6":  insert_record(conn)
            elif choice == "7":  update_record(conn)
            elif choice == "8":  delete_record(conn)
            elif choice == "9":  search_records(conn)
            elif choice == "10": reinitialize_database(conn)
            elif choice == "11": demo_analytical_query(conn)
            elif choice == "12": demo_stored_procedure(conn)
            elif choice == "13": demo_rls(conn)
            elif choice == "14":
                print("\n  Exiting application. Goodbye!")
                break
            else:
                print("  Invalid option. Please choose a number from 1 to 14.")

            input("\n  Press Enter to continue...")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
