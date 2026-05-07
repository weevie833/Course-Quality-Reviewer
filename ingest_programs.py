"""
Populates program structure: programs, program_courses join table.
Safe to re-run — clears and rebuilds program data only.
Run: python3 ingest_programs.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "program.db"

# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------
PROGRAMS = [
    # (short_name, full_name, degree_type)
    ("Leadership",     "Master of Science in Leadership", "Master's"),
    ("Leadership-HRM", "Master of Science in Leadership — Human Resources Management Track", "Master's"),
    ("Leadership-ITM", "Master of Science in Leadership — Information Technology Management Track", "Master's"),
    ("Project Management", "Master of Science in Project Management", "Master's"),
]

# ---------------------------------------------------------------------------
# Course stubs for courses not yet in canvas_courses
# (course_id, title, required_flag)
# ---------------------------------------------------------------------------
COURSE_STUBS = [
    ("APST-805", "Grant Writing", 0),
    ("CMPL-801", "Principles of Information Technology for IT Managers", 0),
    ("CMPL-802", "Managing Virtualization and Cloud Systems", 0),
    ("CMPL-810", "Current and Emerging Technologies", 0),
    ("CMPL-815", "Managing Artificial Intelligence", 0),
    ("CMPL-820", "Information Privacy, Security, and Continuity", 0),
    ("CMPL-825", "Designing and Analyzing Information Systems", 0),
    ("CMPL-850", "Managing Information Technology Capstone", 0),
    ("LD-827",   "Leading and Governing Nonprofit Organizations", 0),
    ("MGMT-830", "Strategic Planning and Financial Management", 0),
    ("OPS-800",  "Principles of Operations Management", 0),
    ("SCM-805",  "Supply Chain Management", 0),
]

# ---------------------------------------------------------------------------
# Program → course mappings
# role: "required" | "elective"
# or_group: None = unconditional; same integer = choose one from group
# (short_name, course_id, role, or_group)
# ---------------------------------------------------------------------------
PROGRAM_COURSES = [
    # --- Leadership ---
    ("Leadership", "LD-820",  "required", None),
    ("Leadership", "LD-821",  "required", None),
    ("Leadership", "COM-800", "required", None),
    ("Leadership", "LD-823",  "required", None),
    ("Leadership", "LD-804",  "required", None),
    ("Leadership", "LD-810",  "required", None),
    ("Leadership", "LD-850",  "required", None),
    ("Leadership", "APST-805","elective", None),
    ("Leadership", "LD-806",  "elective", None),
    ("Leadership", "LD-825",  "elective", None),
    ("Leadership", "LD-827",  "elective", None),
    ("Leadership", "LD-831",  "elective", None),
    ("Leadership", "LD-832",  "elective", None),
    ("Leadership", "MGMT-805","elective", None),
    ("Leadership", "PM-800",  "elective", None),
    ("Leadership", "PM-811",  "elective", None),

    # --- Leadership-HRM ---
    ("Leadership-HRM", "HRM-805",  "required", None),
    ("Leadership-HRM", "HRM-810",  "required", 1),   # HRM-810 or HRM-830
    ("Leadership-HRM", "HRM-830",  "required", 1),   # HRM-810 or HRM-830
    ("Leadership-HRM", "HRM-815",  "required", None),
    ("Leadership-HRM", "LD-804",   "required", None),
    ("Leadership-HRM", "LD-820",   "required", None),
    ("Leadership-HRM", "LD-823",   "required", None),
    ("Leadership-HRM", "MGMT-805", "required", None),
    ("Leadership-HRM", "LD-850",   "required", None),
    ("Leadership-HRM", "HRM-820",  "elective", None),
    ("Leadership-HRM", "HRM-821",  "elective", None),
    ("Leadership-HRM", "HRM-822",  "elective", None),

    # --- Leadership-ITM ---
    ("Leadership-ITM", "CMPL-801",  "required", None),
    ("Leadership-ITM", "CMPL-820",  "required", None),
    ("Leadership-ITM", "CMPL-825",  "required", None),
    ("Leadership-ITM", "LD-804",    "required", None),
    ("Leadership-ITM", "LD-810",    "required", None),
    ("Leadership-ITM", "LD-820",    "required", None),
    ("Leadership-ITM", "MGMT-830",  "required", None),
    ("Leadership-ITM", "PM-800",    "required", None),
    ("Leadership-ITM", "CMPL-850",  "required", None),
    ("Leadership-ITM", "CMPL-802",  "elective", None),
    ("Leadership-ITM", "CMPL-810",  "elective", None),
    ("Leadership-ITM", "CMPL-815",  "elective", None),

    # --- Project Management ---
    ("Project Management", "PM-800",  "required", None),
    ("Project Management", "PM-811",  "required", None),
    ("Project Management", "PM-813",  "required", None),
    ("Project Management", "PM-815",  "required", None),
    ("Project Management", "PM-817",  "required", None),
    ("Project Management", "PM-819",  "required", None),
    ("Project Management", "LD-804",  "required", None),
    ("Project Management", "PM-850",  "required", None),
    ("Project Management", "LD-810",  "elective", None),
    ("Project Management", "LD-821",  "elective", None),
    ("Project Management", "LD-832",  "elective", None),
    ("Project Management", "OPS-800", "elective", None),
    ("Project Management", "PM-820",  "elective", None),
    ("Project Management", "PM-821",  "elective", None),
    ("Project Management", "PM-830",  "elective", None),
    ("Project Management", "PM-832",  "elective", None),
    ("Project Management", "SCM-805", "elective", None),
]


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")

    # Add short_name column to programs if not present
    cols = [r[1] for r in conn.execute("PRAGMA table_info(programs)").fetchall()]
    if "short_name" not in cols:
        conn.execute("ALTER TABLE programs ADD COLUMN short_name TEXT")

    # Create program_courses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS program_courses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL REFERENCES programs(id),
            course_id  TEXT NOT NULL,
            role       TEXT NOT NULL CHECK(role IN ('required','elective')),
            or_group   INTEGER,
            UNIQUE(program_id, course_id)
        )
    """)

    # Clear existing program data (keep courses table intact)
    conn.execute("DELETE FROM program_courses")
    conn.execute("DELETE FROM programs")
    conn.commit()

    # Insert course stubs (courses without canvas content yet)
    for course_id, title, req in COURSE_STUBS:
        conn.execute(
            "INSERT OR IGNORE INTO courses (course_id, title, required) VALUES (?, ?, ?)",
            (course_id, title, req)
        )
    conn.commit()

    # Insert programs and build short_name → id map
    program_id_map = {}
    for short_name, full_name, degree_type in PROGRAMS:
        cur = conn.execute(
            "INSERT INTO programs (name, degree_type, short_name) VALUES (?, ?, ?)",
            (full_name, degree_type, short_name)
        )
        program_id_map[short_name] = cur.lastrowid

    # Insert program_courses
    skipped = []
    for short_name, course_id, role, or_group in PROGRAM_COURSES:
        program_id = program_id_map[short_name]
        # Verify course exists
        exists = conn.execute(
            "SELECT 1 FROM courses WHERE course_id=?", (course_id,)
        ).fetchone()
        if not exists:
            skipped.append((short_name, course_id))
            continue
        conn.execute(
            "INSERT OR IGNORE INTO program_courses (program_id, course_id, role, or_group) "
            "VALUES (?, ?, ?, ?)",
            (program_id, course_id, role, or_group)
        )

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    # Summary
    for short_name, pid in program_id_map.items():
        req = conn.execute(
            "SELECT COUNT(*) FROM program_courses WHERE program_id=? AND role='required'", (pid,)
        ).fetchone()[0]
        elec = conn.execute(
            "SELECT COUNT(*) FROM program_courses WHERE program_id=? AND role='elective'", (pid,)
        ).fetchone()[0]
        print(f"  {short_name}: {req} required, {elec} elective")

    if skipped:
        print(f"\nSkipped (course not in DB):")
        for s, c in skipped:
            print(f"  {s} — {c}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
