"""
Updates P/L competency descriptions and inserts rating level descriptors
from the PM-Outcome Set.csv file.

CSV columns:
  vendor_guid  — PM-1.01.1 format → normalized to 1.1.1 for DB lookup
  title        — short name (not used; DB name already set)
  description  — proficiency indicator text → competencies.description
  Level 5      — Exemplary   → competency_level_descriptors level=5
  Level 4      — Proficient  → level=4
  Level 3      — Basic       → level=3
  Level 2      — Emerging    → level=2
  Level 1      — Novice      → level=1

Safe to re-run: clears existing P/L level descriptors and descriptions
before inserting.
"""

import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "program.db"
CSV_PATH = Path("/Users/stevecovello/Desktop/Claude-Codex Projects/_Program Intelligence Interface/PM Program/PM-Outcome Set.csv")

LEVEL_COLS = {
    5: "Level 5",
    4: "Level 4",
    3: "Level 3",
    2: "Level 2",
    1: "Level 1",
}


def normalize_code(vendor_guid: str) -> str:
    """PM-1.01.1  →  1.1.1  (strip prefix, remove leading zeros per segment)"""
    code = vendor_guid.strip()
    if code.upper().startswith("PM-"):
        code = code[3:]
    parts = code.split(".")
    return ".".join(str(int(p)) for p in parts)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load all P/L competency IDs by normalized code
    rows = conn.execute("""
        SELECT c.id, c.code
        FROM competencies c
        JOIN competency_categories cc ON c.category_id = cc.id
        WHERE cc.letter IN ('P', 'L')
    """).fetchall()
    comp_by_code = {normalize_code(r["code"]): r["id"] for r in rows}
    print(f"P/L competencies in DB: {len(comp_by_code)}")

    # Clear existing P/L level descriptors and descriptions
    conn.execute("""
        DELETE FROM competency_level_descriptors
        WHERE competency_id IN (
            SELECT c.id FROM competencies c
            JOIN competency_categories cc ON c.category_id = cc.id
            WHERE cc.letter IN ('P', 'L')
        )
    """)
    conn.execute("""
        UPDATE competencies SET description = ''
        WHERE id IN (
            SELECT c.id FROM competencies c
            JOIN competency_categories cc ON c.category_id = cc.id
            WHERE cc.letter IN ('P', 'L')
        )
    """)

    matched = 0
    unmatched = []
    desc_updated = 0
    levels_inserted = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_code = row.get("vendor_guid", "").strip()
            if not raw_code:
                continue

            norm_code = normalize_code(raw_code)
            comp_id = comp_by_code.get(norm_code)
            if comp_id is None:
                unmatched.append(f"{raw_code} → {norm_code}")
                continue

            matched += 1

            # Update description
            desc = row.get("description", "").strip()
            if desc:
                conn.execute(
                    "UPDATE competencies SET description = ? WHERE id = ?",
                    (desc, comp_id),
                )
                desc_updated += 1

            # Insert level descriptors
            for level_num, col_name in LEVEL_COLS.items():
                descriptor = row.get(col_name, "").strip()
                if descriptor:
                    conn.execute(
                        "INSERT INTO competency_level_descriptors "
                        "(competency_id, level, descriptor) VALUES (?, ?, ?)",
                        (comp_id, level_num, descriptor),
                    )
                    levels_inserted += 1

    conn.commit()
    conn.close()

    print(f"Matched:           {matched}")
    print(f"Descriptions set:  {desc_updated}")
    print(f"Level descriptors: {levels_inserted}")
    if unmatched:
        print(f"\nUnmatched codes ({len(unmatched)}):")
        for u in unmatched:
            print(f"  {u}")
    else:
        print("\nNo unmatched codes.")


if __name__ == "__main__":
    main()
