"""
Ingestion script: parses all canvas_courses HTML files and plos_clos.txt into SQLite.
Run once (or re-run to rebuild): python3 ingest.py
"""

import os
import re
import sqlite3
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
COURSES_DIR = BASE_DIR / "canvas_courses"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "program.db"
PLOS_CLOS_PATH = DATA_DIR / "plos_clos.txt"

REQUIRED_COURSES = {
    "HRM-805", "HRM-810", "HRM-815", "HRM-830",
    "LD-804", "LD-820", "LD-823", "LD-850", "MGMT-805",
}
ELECTIVE_COURSES = {"HRM-820", "HRM-821", "HRM-822"}

CANVAS_NS = "http://canvas.instructure.com/xsd/cccv1p0"

COURSE_TITLES = {
    "HRM-805": "Managing Human Resources in a Global Economy",
    "HRM-810": "Business Acumen: Role of HR in Business",
    "HRM-815": "Employment Law and Ethics",
    "HRM-820": "Recruitment and Selection",
    "HRM-821": "Strategic Rewards and Performance Management",
    "HRM-822": "Talent Management and Development",
    "HRM-830": "HR Technology and People Analytics",
    "LD-804":  "Leading Teams",
    "LD-820":  "Cultivating Your Leadership Capabilities",
    "LD-823":  "Emergence of a Strategic Leader",
    "LD-850":  "Leadership Integrative Capstone",
    "MGMT-805": "Organizational Behavior",
}


# ---------------------------------------------------------------------------
# HTML → plain text
# ---------------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts).strip()


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    return re.sub(r"\s+", " ", p.get_text()).strip()


# ---------------------------------------------------------------------------
# Metadata comment parser
# ---------------------------------------------------------------------------

COMMENT_RE = re.compile(r"<!--\s*([A-Z\-]+):\s*(.*?)\s*-->")

def parse_metadata(raw: str) -> dict:
    meta = {}
    for key, value in COMMENT_RE.findall(raw[:1000]):
        meta[key] = value
    return meta


# ---------------------------------------------------------------------------
# Rubric XML parser
# ---------------------------------------------------------------------------

def parse_rubric_xml(raw: str) -> tuple[str, float, list[dict]]:
    """Returns (title, points_possible, criteria_list)."""
    # Strip leading HTML comments before the XML
    xml_start = raw.find("<ns0:rubric")
    if xml_start == -1:
        xml_start = raw.find("<rubric")
    if xml_start == -1:
        return ("", 0.0, [])
    xml_body = raw[xml_start:]

    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError:
        return ("", 0.0, [])

    ns = {"c": CANVAS_NS}

    title = (root.findtext("c:title", namespaces=ns) or "").strip()
    pts_text = root.findtext("c:points_possible", namespaces=ns) or "0"
    try:
        points_possible = float(pts_text)
    except ValueError:
        points_possible = 0.0

    criteria = []
    for crit in root.findall(".//c:criterion", namespaces=ns):
        desc = (crit.findtext("c:description", namespaces=ns) or "").strip()
        pts = crit.findtext("c:points", namespaces=ns) or "0"
        try:
            crit_pts = float(pts)
        except ValueError:
            crit_pts = 0.0

        ratings = []
        for r in crit.findall(".//c:rating", namespaces=ns):
            r_desc = (r.findtext("c:description", namespaces=ns) or "").strip()
            r_long = (r.findtext("c:long_description", namespaces=ns) or "").strip()
            r_pts_text = r.findtext("c:points", namespaces=ns) or "0"
            try:
                r_pts = float(r_pts_text)
            except ValueError:
                r_pts = 0.0
            ratings.append({"description": r_desc, "long_description": r_long, "points": r_pts})

        criteria.append({
            "description": desc,
            "points": crit_pts,
            "ratings": ratings,
        })

    return (title, points_possible, criteria)


# ---------------------------------------------------------------------------
# PLO/CLO parser
# ---------------------------------------------------------------------------

def parse_plos_clos(path: Path) -> tuple[list[dict], list[dict]]:
    """Returns (plos, clos).
    plos: [{number, text}]
    clos: [{course_id, number, text}]
    """
    text = path.read_text()
    plos = []
    clos = []

    current_course = None
    clo_number = 0

    plo_re = re.compile(r"^PLO\s+(\d+):\s+(.+)$")
    clo_re = re.compile(r"^CLO\s+(\d+):\s+(.+)$")
    course_re = re.compile(r"^(HRM-\d+|LD-\d+|MGMT-\d+)\s")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m = plo_re.match(line)
        if m:
            plos.append({"number": int(m.group(1)), "text": m.group(2).strip()})
            continue

        m = course_re.match(line)
        if m:
            current_course = m.group(1)
            clo_number = 0
            continue

        m = clo_re.match(line)
        if m and current_course:
            clos.append({
                "course_id": current_course,
                "number": int(m.group(1)),
                "text": m.group(2).strip(),
            })
            continue

    return plos, clos


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS programs (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    degree_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY,
    course_id   TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    required    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS course_items (
    id           INTEGER PRIMARY KEY,
    course_id    TEXT NOT NULL,
    content_type TEXT NOT NULL,   -- Assignment | Discussion | Page
    module       TEXT,
    title        TEXT NOT NULL,
    body_text    TEXT,
    rubric_ref   TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS rubrics (
    id              INTEGER PRIMARY KEY,
    course_id       TEXT NOT NULL,
    rubric_name     TEXT NOT NULL,
    points_possible REAL,
    UNIQUE(course_id, rubric_name),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS rubric_criteria (
    id          INTEGER PRIMARY KEY,
    rubric_id   INTEGER NOT NULL,
    description TEXT NOT NULL,
    points      REAL,
    ratings_json TEXT,
    FOREIGN KEY (rubric_id) REFERENCES rubrics(id)
);

CREATE TABLE IF NOT EXISTS item_rubric_links (
    item_id   INTEGER NOT NULL,
    rubric_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, rubric_id),
    FOREIGN KEY (item_id)   REFERENCES course_items(id),
    FOREIGN KEY (rubric_id) REFERENCES rubrics(id)
);

CREATE TABLE IF NOT EXISTS plos (
    id     INTEGER PRIMARY KEY,
    number INTEGER NOT NULL,
    text   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clos (
    id        INTEGER PRIMARY KEY,
    course_id TEXT NOT NULL,
    number    INTEGER NOT NULL,
    text      TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS plo_clo_links (
    id         INTEGER PRIMARY KEY,
    plo_id     INTEGER NOT NULL,
    clo_id     INTEGER NOT NULL,
    strength   TEXT,   -- strong | moderate | weak
    rationale  TEXT,
    FOREIGN KEY (plo_id) REFERENCES plos(id),
    FOREIGN KEY (clo_id) REFERENCES clos(id)
);
"""


def init_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    conn.commit()


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

def ingest_program(conn: sqlite3.Connection):
    conn.execute(
        "INSERT OR IGNORE INTO programs (id, name, degree_type) VALUES (1, ?, ?)",
        ("Master of Science in Leadership — Human Resources Management Track", "Master's"),
    )
    conn.commit()


def ingest_courses(conn: sqlite3.Connection):
    for cid, title in COURSE_TITLES.items():
        required = 1 if cid in REQUIRED_COURSES else 0
        conn.execute(
            "INSERT OR IGNORE INTO courses (course_id, title, required) VALUES (?, ?, ?)",
            (cid, title, required),
        )
    conn.commit()


def ingest_plos_clos(conn: sqlite3.Connection):
    plos, clos = parse_plos_clos(PLOS_CLOS_PATH)

    for p in plos:
        conn.execute(
            "INSERT OR IGNORE INTO plos (number, text) VALUES (?, ?)",
            (p["number"], p["text"]),
        )

    for c in clos:
        conn.execute(
            "INSERT OR IGNORE INTO clos (course_id, number, text) VALUES (?, ?, ?)",
            (c["course_id"], c["number"], c["text"]),
        )

    conn.commit()
    return len(plos), len(clos)


def ingest_one_course(conn: sqlite3.Connection, course_id: str, course_dir: Path) -> dict:
    """Ingest all HTML files for a single course directory. Returns counts dict."""
    rubric_cache: dict[tuple, int] = {}  # (course_id, rubric_name) -> rubric_id
    items_inserted = rubrics_inserted = criteria_inserted = links_inserted = 0

    for html_file in sorted(course_dir.glob("*.html")):
        raw = html_file.read_text(encoding="utf-8", errors="replace")
        meta = parse_metadata(raw)
        content_type = meta.get("CONTENT-TYPE", "").strip()

        if content_type == "Rubric":
            rubric_name = meta.get("RUBRIC-NAME") or meta.get("TITLE", "")
            title, pts, criteria = parse_rubric_xml(raw)
            if not title:
                title = rubric_name

            key = (course_id, title)
            if key not in rubric_cache:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO rubrics (course_id, rubric_name, points_possible) "
                    "VALUES (?, ?, ?)",
                    (course_id, title, pts),
                )
                if cur.lastrowid:
                    rubric_id = cur.lastrowid
                    rubrics_inserted += 1
                else:
                    row = conn.execute(
                        "SELECT id FROM rubrics WHERE course_id=? AND rubric_name=?",
                        (course_id, title),
                    ).fetchone()
                    rubric_id = row[0]
                rubric_cache[key] = rubric_id
            else:
                rubric_id = rubric_cache[key]

            for crit in criteria:
                conn.execute(
                    "INSERT INTO rubric_criteria (rubric_id, description, points, ratings_json) "
                    "VALUES (?, ?, ?, ?)",
                    (rubric_id, crit["description"], crit["points"], json.dumps(crit["ratings"])),
                )
                criteria_inserted += 1

        elif content_type in ("Assignment", "Discussion", "Page"):
            title = meta.get("TITLE", html_file.stem)
            module = meta.get("MODULE", "")
            rubric_ref = meta.get("RUBRIC-REF", "")
            body_text = html_to_text(raw)

            cur = conn.execute(
                "INSERT INTO course_items (course_id, content_type, module, title, body_text, rubric_ref) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (course_id, content_type, module, title, body_text, rubric_ref),
            )
            item_id = cur.lastrowid
            items_inserted += 1

            if rubric_ref:
                key = (course_id, rubric_ref)
                if key in rubric_cache:
                    conn.execute(
                        "INSERT OR IGNORE INTO item_rubric_links (item_id, rubric_id) VALUES (?, ?)",
                        (item_id, rubric_cache[key]),
                    )
                    links_inserted += 1

    conn.commit()

    # Second pass: resolve rubric_ref links not resolved during the first pass (forward refs)
    unlinked = conn.execute(
        "SELECT ci.id, ci.rubric_ref FROM course_items ci "
        "WHERE ci.course_id=? AND ci.rubric_ref != '' "
        "AND ci.id NOT IN (SELECT item_id FROM item_rubric_links)",
        (course_id,)
    ).fetchall()
    for item_id, rref in unlinked:
        row = conn.execute(
            "SELECT id FROM rubrics WHERE course_id=? AND rubric_name=?", (course_id, rref)
        ).fetchone()
        if row:
            conn.execute(
                "INSERT OR IGNORE INTO item_rubric_links (item_id, rubric_id) VALUES (?, ?)",
                (item_id, row[0]),
            )
            links_inserted += 1
    conn.commit()

    return {
        "items": items_inserted,
        "rubrics": rubrics_inserted,
        "criteria": criteria_inserted,
        "links": links_inserted,
    }


def ingest_course_files(conn: sqlite3.Connection):
    totals = {"items": 0, "rubrics": 0, "criteria": 0, "links": 0}

    for course_dir in sorted(COURSES_DIR.iterdir()):
        if not course_dir.is_dir():
            continue
        counts = ingest_one_course(conn, course_dir.name, course_dir)
        for k in totals:
            totals[k] += counts[k]

    return totals["items"], totals["rubrics"], totals["criteria"], totals["links"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    DATA_DIR.mkdir(exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("Initializing schema...")
    init_db(conn)

    print("Inserting program...")
    ingest_program(conn)

    print("Inserting courses...")
    ingest_courses(conn)

    print("Inserting PLOs and CLOs...")
    n_plos, n_clos = ingest_plos_clos(conn)
    print(f"  {n_plos} PLOs, {n_clos} CLOs")

    print("Ingesting course files...")
    items, rubrics, criteria, links = ingest_course_files(conn)
    print(f"  {items} course items")
    print(f"  {rubrics} rubrics, {criteria} rubric criteria")
    print(f"  {links} item→rubric links")

    conn.close()
    print(f"\nDone. Database written to: {DB_PATH}")


if __name__ == "__main__":
    main()
