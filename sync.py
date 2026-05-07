"""
Automatic course sync: fingerprint-based change detection for canvas_courses/.

Called at FastAPI startup via main.py lifespan. Checks every course folder in
canvas_courses/ against a stored fingerprint (stat-based, no file reads). If a
folder is new or any file has changed, the course is wiped and re-ingested.

New courses (not in COURSE_TITLES) are auto-registered in the courses table using
the title found in the extraction log JSON written by the Cowork extractor. If no
log is present, the course_id is used as a placeholder title.

Competency links are preserved across re-ingests by saving title→id pairs and
restoring them after new item IDs are assigned.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ingest import COURSE_TITLES, COURSES_DIR, DB_PATH, REQUIRED_COURSES, ELECTIVE_COURSES, ingest_one_course

# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

def compute_fingerprint(course_dir: Path) -> str:
    """MD5 of sorted (filename, mtime, size) for all .html files — no file reads."""
    entries = []
    for f in sorted(course_dir.glob("*.html")):
        stat = f.stat()
        entries.append(f"{f.name}:{stat.st_mtime:.3f}:{stat.st_size}")
    blob = "\n".join(entries).encode()
    return hashlib.md5(blob).hexdigest()


# ---------------------------------------------------------------------------
# Ingest log table
# ---------------------------------------------------------------------------

def ensure_ingest_log_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS course_ingest_log (
            course_id    TEXT PRIMARY KEY,
            fingerprint  TEXT NOT NULL,
            ingested_at  TEXT NOT NULL
        )
    """)
    conn.commit()


def get_stored_fingerprint(conn: sqlite3.Connection, course_id: str) -> str | None:
    row = conn.execute(
        "SELECT fingerprint FROM course_ingest_log WHERE course_id=?", (course_id,)
    ).fetchone()
    return row[0] if row else None


def set_fingerprint(conn: sqlite3.Connection, course_id: str, fingerprint: str):
    conn.execute("""
        INSERT INTO course_ingest_log (course_id, fingerprint, ingested_at)
        VALUES (?, ?, ?)
        ON CONFLICT(course_id) DO UPDATE
            SET fingerprint=excluded.fingerprint,
                ingested_at=excluded.ingested_at
    """, (course_id, fingerprint, datetime.now(timezone.utc).isoformat()))
    conn.commit()


# ---------------------------------------------------------------------------
# Competency link preservation
# ---------------------------------------------------------------------------

def save_competency_links(conn: sqlite3.Connection, course_id: str) -> list[dict]:
    """Read title→competency_id pairs before wiping course data."""
    try:
        rows = conn.execute("""
            SELECT ci.title, icl.competency_id
            FROM item_competency_links icl
            JOIN course_items ci ON icl.item_id = ci.id
            WHERE ci.course_id = ?
        """, (course_id,)).fetchall()
        return [{"title": row[0], "competency_id": row[1]} for row in rows]
    except sqlite3.OperationalError:
        # item_competency_links table doesn't exist yet — nothing to preserve
        return []


def restore_competency_links(conn: sqlite3.Connection, course_id: str, saved_links: list[dict]):
    """Re-link competencies after re-ingest by matching saved titles to new item IDs."""
    if not saved_links:
        return
    for link in saved_links:
        row = conn.execute(
            "SELECT id FROM course_items WHERE course_id=? AND title=?",
            (course_id, link["title"])
        ).fetchone()
        if row:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO item_competency_links (item_id, competency_id)
                    VALUES (?, ?)
                """, (row[0], link["competency_id"]))
            except sqlite3.OperationalError:
                pass  # table doesn't exist yet
    conn.commit()


# ---------------------------------------------------------------------------
# Per-course delete
# ---------------------------------------------------------------------------

def delete_course_data(conn: sqlite3.Connection, course_id: str):
    """Remove all course-specific rows in dependency order."""
    item_ids = [r[0] for r in conn.execute(
        "SELECT id FROM course_items WHERE course_id=?", (course_id,)
    ).fetchall()]

    if item_ids:
        placeholders = ",".join("?" * len(item_ids))
        conn.execute(
            f"DELETE FROM item_rubric_links WHERE item_id IN ({placeholders})", item_ids
        )
        try:
            conn.execute(
                f"DELETE FROM item_competency_links WHERE item_id IN ({placeholders})",
                item_ids
            )
        except sqlite3.OperationalError:
            pass  # competency tables not yet created
        conn.execute(
            f"DELETE FROM course_items WHERE id IN ({placeholders})", item_ids
        )

    rubric_ids = [r[0] for r in conn.execute(
        "SELECT id FROM rubrics WHERE course_id=?", (course_id,)
    ).fetchall()]

    if rubric_ids:
        placeholders = ",".join("?" * len(rubric_ids))
        conn.execute(
            f"DELETE FROM rubric_criteria WHERE rubric_id IN ({placeholders})", rubric_ids
        )
        conn.execute(
            f"DELETE FROM rubrics WHERE id IN ({placeholders})", rubric_ids
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Course title discovery
# ---------------------------------------------------------------------------

def discover_course_title(course_dir: Path, course_id: str) -> str:
    """
    Read the course title from the Cowork extraction log JSON.
    Falls back to the course_id if no log is present.
    """
    log_file = course_dir / f"{course_id}_extraction-log.json"
    if log_file.exists():
        try:
            data = json.loads(log_file.read_text(encoding="utf-8"))
            title = data.get("course_title", "").strip()
            if title:
                return title
        except (json.JSONDecodeError, OSError):
            pass
    return course_id  # fallback: use the folder name


def ensure_course_registered(conn: sqlite3.Connection, course_id: str, course_dir: Path):
    """Insert the course into the courses table if not already present."""
    existing = conn.execute(
        "SELECT 1 FROM courses WHERE course_id=?", (course_id,)
    ).fetchone()
    if existing:
        return

    # Known courses keep their required/elective designation from COURSE_TITLES
    if course_id in REQUIRED_COURSES:
        required = 1
    elif course_id in ELECTIVE_COURSES:
        required = 0
    else:
        required = 0  # new/unknown courses default to elective

    title = COURSE_TITLES.get(course_id) or discover_course_title(course_dir, course_id)
    conn.execute(
        "INSERT OR IGNORE INTO courses (course_id, title, required) VALUES (?, ?, ?)",
        (course_id, title, required)
    )
    conn.commit()
    print(f"[sync]   Registered new course: {course_id} — {title}")


# ---------------------------------------------------------------------------
# Main sync entry point
# ---------------------------------------------------------------------------

def sync_courses():
    """
    Compare fingerprints for every course folder in canvas_courses/.
    Re-ingest any course whose .html files have changed since last ingest.
    New course folders are auto-registered using the Cowork extraction log.
    Competency links are preserved across re-ingests by title matching.
    """
    if not COURSES_DIR.exists():
        print("[sync] canvas_courses directory not found — skipping")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    ensure_ingest_log_table(conn)

    updated = 0
    skipped = 0

    for course_dir in sorted(COURSES_DIR.iterdir()):
        if not course_dir.is_dir():
            continue
        course_id = course_dir.name

        # Skip folders with no HTML files (empty or non-course directories)
        if not any(course_dir.glob("*.html")):
            continue

        current_fp = compute_fingerprint(course_dir)
        stored_fp = get_stored_fingerprint(conn, course_id)

        if current_fp == stored_fp:
            skipped += 1
            continue

        action = "re-ingesting" if stored_fp else "ingesting (new)"
        print(f"[sync] {course_id}: {action}...")

        ensure_course_registered(conn, course_id, course_dir)
        saved_links = save_competency_links(conn, course_id)
        delete_course_data(conn, course_id)
        counts = ingest_one_course(conn, course_id, course_dir)
        restore_competency_links(conn, course_id, saved_links)
        set_fingerprint(conn, course_id, current_fp)

        updated += 1
        detail = f"{counts['items']} items, {counts['rubrics']} rubrics"
        if saved_links:
            detail += f", {len(saved_links)} competency links restored"
        print(f"[sync]   Done — {detail}")

    conn.close()

    if updated:
        print(f"[sync] Sync complete: {updated} updated, {skipped} unchanged")
    else:
        print(f"[sync] All {skipped} courses are up to date")
