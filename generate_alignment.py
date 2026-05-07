"""
Generates PLO→CLO and CLO→Assignment alignment maps using the Claude API.
Writes results to data/alignment_map.json and populates plo_clo_links in SQLite.

Run after ingest.py:
    python3 generate_alignment.py
"""

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import os
import anthropic

BASE_DIR = Path(__file__).parent

# Load .env manually (handles files without trailing newline)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            _key, _val = _k.strip(), _v.strip()
            if _val and not os.environ.get(_key):
                os.environ[_key] = _val
DB_PATH = BASE_DIR / "data" / "program.db"
OUTPUT_PATH = BASE_DIR / "data" / "alignment_map.json"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def load_course_programs(conn) -> dict[str, list[str]]:
    """Returns {course_id: [program_short_name, ...]} for all program-course memberships."""
    rows = conn.execute("""
        SELECT pc.course_id, p.short_name
        FROM program_courses pc
        JOIN programs p ON pc.program_id = p.id
    """).fetchall()
    result: dict[str, list[str]] = {}
    for r in rows:
        result.setdefault(r[0], []).append(r[1])
    return result


def load_plos_for_programs(conn, program_short_names: list[str]) -> list[dict]:
    """Load PLOs for the given programs, including their DB id and program name."""
    if not program_short_names:
        return []
    placeholders = ",".join("?" * len(program_short_names))
    rows = conn.execute(f"""
        SELECT plo.id, plo.number, plo.text, p.short_name AS program
        FROM plos plo
        JOIN programs p ON plo.program_id = p.id
        WHERE p.short_name IN ({placeholders})
        ORDER BY p.short_name, plo.number
    """, program_short_names).fetchall()
    return [{"id": r[0], "number": r[1], "text": r[2], "program": r[3]} for r in rows]


def load_clos_for_course(conn, course_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT id, number, text FROM clos WHERE course_id=? ORDER BY number",
        (course_id,),
    ).fetchall()
    return [{"id": r[0], "number": r[1], "text": r[2]} for r in rows]


def load_items_for_course(conn, course_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT id, content_type, module, title, body_text FROM course_items "
        "WHERE course_id=? AND content_type IN ('Assignment','Discussion') "
        "ORDER BY content_type, title",
        (course_id,),
    ).fetchall()
    return [
        {
            "id": r[0],
            "content_type": r[1],
            "module": r[2] or "",
            "title": r[3],
            "body_snippet": (r[4] or "")[:600],
        }
        for r in rows
    ]


def load_course_ids(conn) -> list[str]:
    rows = conn.execute("SELECT course_id FROM courses ORDER BY course_id").fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Claude API calls with tool_use for structured output
# ---------------------------------------------------------------------------

PLO_CLO_TOOL = {
    "name": "record_plo_clo_alignments",
    "description": "Record the alignment between PLOs and CLOs for a course.",
    "input_schema": {
        "type": "object",
        "properties": {
            "alignments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "clo_number": {"type": "integer"},
                        "plo_alignments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "plo_id": {"type": "integer"},
                                    "strength": {
                                        "type": "string",
                                        "enum": ["strong", "moderate", "weak", "none"],
                                    },
                                    "rationale": {"type": "string"},
                                },
                                "required": ["plo_id", "strength", "rationale"],
                            },
                        },
                    },
                    "required": ["clo_number", "plo_alignments"],
                },
            }
        },
        "required": ["alignments"],
    },
}

CLO_ITEM_TOOL = {
    "name": "record_clo_item_alignments",
    "description": "Record the alignment between CLOs and course assignments/discussions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "alignments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "integer"},
                        "clo_alignments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "clo_number": {"type": "integer"},
                                    "strength": {
                                        "type": "string",
                                        "enum": ["strong", "moderate", "weak", "none"],
                                    },
                                    "rationale": {"type": "string"},
                                },
                                "required": ["clo_number", "strength", "rationale"],
                            },
                        },
                    },
                    "required": ["item_id", "clo_alignments"],
                },
            }
        },
        "required": ["alignments"],
    },
}


def call_plo_clo(course_id: str, plos: list[dict], clos: list[dict]) -> list[dict]:
    """Returns list of {clo_number, plo_alignments:[{plo_id, strength, rationale}]}"""
    # PLOs include their DB id so Claude can return unambiguous references across programs
    plo_block = "\n".join(
        f"[ID:{p['id']}] PLO {p['number']} ({p['program']}): {p['text']}" for p in plos
    )
    clo_block = "\n".join(f"CLO {c['number']}: {c['text']}" for c in clos)

    prompt = f"""You are an instructional design expert analyzing curriculum alignment for a graduate program.

Course: {course_id}

PROGRAM LEARNING OUTCOMES (PLOs) — use the exact integer ID shown in brackets when recording alignments:
{plo_block}

COURSE LEARNING OUTCOMES (CLOs) for {course_id}:
{clo_block}

For each CLO, assess its alignment with each PLO using these criteria:
- strong: The CLO directly and substantially addresses the PLO's intent; a student completing this CLO is clearly building toward that PLO.
- moderate: The CLO partially addresses the PLO or addresses a closely related skill; meaningful but not direct alignment.
- weak: There is a tangential or indirect connection, but the CLO's primary focus is elsewhere.
- none: No meaningful alignment.

Be discriminating — most CLO/PLO pairs should be "none" or "weak". Reserve "strong" for clear, direct alignment.
Record your assessment using the provided tool. For plo_id, use the integer ID from the brackets, not the PLO number."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        tools=[PLO_CLO_TOOL],
        tool_choice={"type": "tool", "name": "record_plo_clo_alignments"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_plo_clo_alignments":
            result = block.input.get("alignments")
            if result is None:
                print(f"\n  [WARN] Unexpected tool output keys: {list(block.input.keys())}")
                return []
            return result
    print(f"\n  [WARN] No tool_use block found in response (stop_reason={response.stop_reason})")
    return []


def call_clo_items(course_id: str, clos: list[dict], items: list[dict]) -> list[dict]:
    """Returns list of {item_id, clo_alignments:[{clo_number, strength, rationale}]}"""
    clo_block = "\n".join(f"CLO {c['number']}: {c['text']}" for c in clos)
    item_block = "\n\n".join(
        f"[ID:{item['id']}] {item['content_type']} — {item['title']}\n"
        f"Module: {item['module']}\n"
        f"Description: {item['body_snippet']}"
        for item in items
    )

    prompt = f"""You are an instructional design expert analyzing curriculum alignment for a graduate program.

Course: {course_id}

COURSE LEARNING OUTCOMES (CLOs):
{clo_block}

COURSE ITEMS (Assignments and Discussions):
{item_block}

For each course item, assess its alignment with each CLO:
- strong: The item directly requires students to demonstrate the CLO; it is a primary vehicle for that outcome.
- moderate: The item partially addresses the CLO or requires related skills; it contributes but is not the primary vehicle.
- weak: The item touches on the CLO incidentally or as background context.
- none: No meaningful alignment.

Use the exact item IDs shown in brackets. Be discriminating — most item/CLO pairs should be "none".
Record your assessment using the provided tool."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        tools=[CLO_ITEM_TOOL],
        tool_choice={"type": "tool", "name": "record_clo_item_alignments"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_clo_item_alignments":
            result = block.input.get("alignments")
            if result is None:
                print(f"\n  [WARN] Unexpected tool output keys: {list(block.input.keys())}")
                return []
            return result
    print(f"\n  [WARN] No tool_use block found (stop_reason={response.stop_reason})")
    return []


# ---------------------------------------------------------------------------
# Persist to SQLite
# ---------------------------------------------------------------------------

def save_plo_clo_links(conn, clos_by_course: dict, plo_clo_results: list[dict]):
    """plo_clo_results: [{course_id, alignments:[{clo_number, plo_alignments:[{plo_id, ...}]}]}]"""
    conn.execute("DELETE FROM plo_clo_links")
    for entry in plo_clo_results:
        course_id = entry["course_id"]
        clos = clos_by_course.get(course_id, [])
        clo_by_num = {c["number"]: c["id"] for c in clos}

        for aln in entry["alignments"]:
            clo_id = clo_by_num.get(aln["clo_number"])
            if not clo_id:
                continue
            for pa in aln["plo_alignments"]:
                if pa["strength"] == "none":
                    continue
                plo_id = pa.get("plo_id")
                if not plo_id:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO plo_clo_links (plo_id, clo_id, strength, rationale) "
                    "VALUES (?,?,?,?)",
                    (plo_id, clo_id, pa["strength"], pa["rationale"]),
                )
    conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import sys
    resume = "--resume" in sys.argv

    conn = sqlite3.connect(DB_PATH)
    course_ids = load_course_ids(conn)
    clos_by_course = {cid: load_clos_for_course(conn, cid) for cid in course_ids}
    course_programs = load_course_programs(conn)

    # Load existing map when resuming; otherwise start fresh
    if resume and OUTPUT_PATH.exists():
        alignment_map = json.loads(OUTPUT_PATH.read_text())
        print("Resuming from existing alignment_map.json")
    else:
        alignment_map = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "plo_clo_alignments": [],
            "clo_item_alignments": [],
        }

    done_plo_clo = {e["course_id"] for e in alignment_map["plo_clo_alignments"]}
    done_clo_item = {e["course_id"] for e in alignment_map["clo_item_alignments"]}
    plo_clo_results = list(alignment_map["plo_clo_alignments"])

    print(f"Generating PLO→CLO alignments ({len(course_ids)} courses)...")
    for i, course_id in enumerate(course_ids, 1):
        if course_id in done_plo_clo:
            print(f"  [{i}/{len(course_ids)}] {course_id} — already done, skipping")
            continue

        clos = clos_by_course[course_id]
        if not clos:
            print(f"  [{i}/{len(course_ids)}] {course_id} — no CLOs, skipping")
            continue

        programs_for_course = course_programs.get(course_id, [])
        if not programs_for_course:
            print(f"  [{i}/{len(course_ids)}] {course_id} — no program membership, skipping")
            continue

        plos = load_plos_for_programs(conn, programs_for_course)
        if not plos:
            print(f"  [{i}/{len(course_ids)}] {course_id} — no PLOs for {programs_for_course}, skipping")
            continue

        prog_label = ", ".join(programs_for_course)
        print(f"  [{i}/{len(course_ids)}] {course_id} ({len(clos)} CLOs, {len(plos)} PLOs from [{prog_label}])...", end=" ", flush=True)
        alignments = call_plo_clo(course_id, plos, clos)
        result = {"course_id": course_id, "alignments": alignments}
        plo_clo_results.append(result)
        alignment_map["plo_clo_alignments"].append(result)
        # Write incrementally so a crash doesn't lose completed work
        OUTPUT_PATH.write_text(json.dumps(alignment_map, indent=2))
        print("done")
        if i < len(course_ids):
            time.sleep(0.5)

    print("\nGenerating CLO→Item alignments...")
    for i, course_id in enumerate(course_ids, 1):
        if course_id in done_clo_item:
            print(f"  [{i}/{len(course_ids)}] {course_id} — already done, skipping")
            continue

        clos = clos_by_course[course_id]
        items = load_items_for_course(conn, course_id)
        if not clos or not items:
            print(f"  [{i}/{len(course_ids)}] {course_id} — skipping (no CLOs or items)")
            continue
        print(f"  [{i}/{len(course_ids)}] {course_id} ({len(clos)} CLOs, {len(items)} items)...", end=" ", flush=True)
        alignments = call_clo_items(course_id, clos, items)
        alignment_map["clo_item_alignments"].append({
            "course_id": course_id,
            "alignments": alignments,
        })
        OUTPUT_PATH.write_text(json.dumps(alignment_map, indent=2))
        print("done")
        if i < len(course_ids):
            time.sleep(0.5)

    print(f"\nalignment_map.json up to date at {OUTPUT_PATH}")

    print("Saving PLO→CLO links to SQLite...")
    save_plo_clo_links(conn, clos_by_course, plo_clo_results)
    n = conn.execute("SELECT COUNT(*) FROM plo_clo_links").fetchone()[0]
    print(f"  {n} links saved (strength != none)")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
