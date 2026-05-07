"""
ingest_alumni.py — Parse SyntheticAlumni.rtf and load alumni table into program.db.

Only stores professionally relevant fields. Contact info, financial data, and
demographic fields are intentionally excluded from the database.

Run:
    python3 ingest_alumni.py
"""

import csv
import io
import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "program.db"

# Update this path if the source file moves
RTF_PATH = Path("/Users/stevecovello/Desktop/Claude Projects/_Program Intelligence Interface/SyntheticAlumni.rtf")


def extract_csv_from_rtf(filepath: Path) -> str:
    """Strip RTF formatting and return the embedded CSV as plain text."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Find the CSV section — starts right after \cf0
    match = re.search(r"\\cf0\s+(.+)", content, re.DOTALL)
    if not match:
        raise ValueError("Could not locate CSV data block in RTF file.")

    csv_section = match.group(1)

    # Drop the trailing RTF closing brace
    csv_section = csv_section.rstrip("}\n\r \t")

    # Strip RTF line-end backslashes and blank lines
    lines = []
    for line in csv_section.split("\n"):
        line = line.rstrip("\\").strip()
        if line:
            lines.append(line)

    return "\n".join(lines)


def ingest():
    if not RTF_PATH.exists():
        print(f"ERROR: Source file not found: {RTF_PATH}")
        return

    print(f"Reading {RTF_PATH.name}...")
    csv_text = extract_csv_from_rtf(RTF_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS alumni")
    c.execute("""
        CREATE TABLE alumni (
            alumni_id          TEXT PRIMARY KEY,
            first_name         TEXT NOT NULL,
            last_name          TEXT NOT NULL,
            preferred_name     TEXT,
            graduation_year    INTEGER,
            degree_type        TEXT,
            program            TEXT,
            honors             TEXT,
            employment_status  TEXT,
            job_title          TEXT,
            employer           TEXT,
            industry           TEXT,
            engagement_level   TEXT,
            volunteer_involvement TEXT,
            event_attendance_2024 INTEGER DEFAULT 0,
            city               TEXT,
            state              TEXT
        )
    """)

    reader = csv.DictReader(io.StringIO(csv_text))

    # Validate header
    required = {"alumni_id", "first_name", "last_name", "job_title", "employer", "industry"}
    if not required.issubset(set(reader.fieldnames or [])):
        missing = required - set(reader.fieldnames or [])
        print(f"ERROR: Missing expected columns: {missing}")
        conn.close()
        return

    count = 0
    for row in reader:
        try:
            attendance = int(row.get("event_attendance_2024", "0").strip() or 0)
        except ValueError:
            attendance = 0

        try:
            grad_year = int(row.get("graduation_year", "0").strip() or 0)
        except ValueError:
            grad_year = 0

        c.execute("""
            INSERT OR REPLACE INTO alumni
            (alumni_id, first_name, last_name, preferred_name,
             graduation_year, degree_type, program, honors,
             employment_status, job_title, employer, industry,
             engagement_level, volunteer_involvement, event_attendance_2024,
             city, state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("alumni_id", "").strip(),
            row.get("first_name", "").strip(),
            row.get("last_name", "").strip(),
            row.get("preferred_name", "").strip() or None,
            grad_year,
            row.get("degree_type", "").strip() or None,
            row.get("program", "").strip() or None,
            row.get("honors", "").strip() or None,
            row.get("employment_status", "").strip() or None,
            row.get("job_title", "").strip() or None,
            row.get("employer", "").strip() or None,
            row.get("industry", "").strip() or None,
            row.get("engagement_level", "").strip() or None,
            row.get("volunteer_involvement", "").strip() or None,
            attendance,
            row.get("city", "").strip() or None,
            row.get("state", "").strip() or None,
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"Done — {count} alumni records loaded into {DB_PATH.name}.")


if __name__ == "__main__":
    ingest()
