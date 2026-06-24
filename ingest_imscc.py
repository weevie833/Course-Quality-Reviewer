#!/usr/bin/env python3
"""
Ingest a Canvas .imscc export directly into the CQR database.

Extracts the ZIP, converts content to CQR-compatible HTML files in
canvas_courses/{course_id}/, then ingests into SQLite using sync.py's
existing pipeline (delete_course_data → ingest_one_course → set_fingerprint).

Usage (CLI):
    python3 ingest_imscc.py /path/to/course.imscc
    python3 ingest_imscc.py /path/to/course.imscc --course-id PM-810

Called from main.py /admin/ingest endpoint for browser uploads.
"""

import argparse
import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

BASE_DIR = Path(__file__).parent
COURSES_DIR = BASE_DIR / "canvas_courses"
DB_PATH = BASE_DIR / "data" / "program.db"

CANVAS_NS = "http://canvas.instructure.com/xsd/cccv1p0"

# Boilerplate page titles to exclude — not course content
EXCLUDED_PAGE_PATTERNS: list[str] = []  # CQR extracts all course content without filtering


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def course_id_from_filename(filename: str) -> str:
    """Extract course ID from .imscc filename: 'pm-810-...' → 'PM-810'."""
    match = re.search(r"([a-z]{2,8})[-_ ]?(\d{3,4})", filename.lower())
    if match:
        return f"{match.group(1).upper()}-{match.group(2)}"
    return re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-") or "unknown"


def safe_extract(zip_ref: zipfile.ZipFile, destination: Path) -> list[str]:
    """Extract ZIP with path-traversal protection."""
    destination = destination.resolve()
    extracted = []
    for member in zip_ref.infolist():
        target = (destination / member.filename).resolve()
        if not str(target).startswith(str(destination)):
            raise ValueError(f"Unsafe zip path: {member.filename}")
        if member.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zip_ref.open(member) as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        extracted.append(member.filename)
    return extracted


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element, name: str, default: str = "") -> str:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return default


def slugify(text: str, max_len: int = 70) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def is_excluded_page(title: str) -> bool:
    normalized = unescape(title).lower()
    return any(re.search(p, normalized) for p in EXCLUDED_PAGE_PATTERNS)


# ---------------------------------------------------------------------------
# Parse manifest
# ---------------------------------------------------------------------------

def parse_manifest_resources(manifest_path: Path) -> dict:
    """Returns identifier → {type, href, files, dependencies}."""
    resources = {}
    root = ET.parse(manifest_path).getroot()
    for el in root.iter():
        if local_name(el.tag) != "resource":
            continue
        ident = el.attrib.get("identifier", "")
        if not ident:
            continue
        resources[ident] = {
            "identifier": ident,
            "type": el.attrib.get("type", ""),
            "href": el.attrib.get("href", ""),
            "files": [
                c.attrib.get("href", "")
                for c in el
                if local_name(c.tag) == "file" and c.attrib.get("href")
            ],
            "dependencies": [
                c.attrib.get("identifierref", "")
                for c in el
                if local_name(c.tag) == "dependency" and c.attrib.get("identifierref")
            ],
        }
    return resources


def detect_course_title(manifest_path: Path, course_id: str) -> str:
    """Read course title from course_settings.xml, falling back to imsmanifest.xml."""
    # course_settings/course_settings.xml has the cleanest title
    settings_path = manifest_path.parent / "course_settings" / "course_settings.xml"
    if settings_path.exists():
        try:
            root = ET.parse(settings_path).getroot()
            el = root.find(f"{{{CANVAS_NS}}}title")
            if el is None:
                el = root.find("title")
            if el is not None and el.text and el.text.strip():
                return el.text.strip()
        except ET.ParseError:
            pass
    # Fallback: first non-empty <string> (lomimscc:string) in imsmanifest.xml
    try:
        root = ET.parse(manifest_path).getroot()
        for el in root.iter():
            if local_name(el.tag) == "string" and el.text and el.text.strip():
                return el.text.strip()
    except ET.ParseError:
        pass
    return course_id


# ---------------------------------------------------------------------------
# Parse module structure
# ---------------------------------------------------------------------------

def parse_module_items(module_meta_path: Path) -> list[dict]:
    """Returns ordered list of module items with type, title, identifierref."""
    root = ET.parse(module_meta_path).getroot()
    items = []
    for module in root:
        if local_name(module.tag) != "module":
            continue
        module_title = child_text(module, "title")
        module_pos = int(child_text(module, "position", "0") or 0)
        for child in module:
            if local_name(child.tag) != "items":
                continue
            for item in child:
                if local_name(item.tag) != "item":
                    continue
                items.append({
                    "moduleTitle": module_title,
                    "modulePosition": module_pos,
                    "contentType": child_text(item, "content_type"),
                    "workflowState": child_text(item, "workflow_state"),
                    "title": child_text(item, "title"),
                    "identifierref": child_text(item, "identifierref"),
                    "position": int(child_text(item, "position", "0") or 0),
                })
    return items


# ---------------------------------------------------------------------------
# Parse rubrics
# ---------------------------------------------------------------------------

def parse_rubrics(rubrics_xml_path: Path) -> dict:
    """Returns identifier → {title, xml_string}. xml_string is serialized with ns0: prefix."""
    if not rubrics_xml_path.exists():
        return {}
    root = ET.parse(rubrics_xml_path).getroot()
    result = {}
    for rubric_el in root:
        if local_name(rubric_el.tag) != "rubric":
            continue
        ident = rubric_el.attrib.get("identifier", "")
        ns = {"c": CANVAS_NS}
        title = (rubric_el.findtext("c:title", namespaces=ns) or child_text(rubric_el, "title")).strip()
        # ET.tostring produces <ns0:rubric xmlns:ns0="..."> which ingest.py expects
        xml_str = ET.tostring(rubric_el, encoding="unicode")
        result[ident] = {"title": title, "xml": xml_str}
    return result


# ---------------------------------------------------------------------------
# Rubric reference lookup
# ---------------------------------------------------------------------------

def get_assignment_rubric_ref(extracted_dir: Path, resource: dict, rubrics: dict) -> str:
    """Read assignment_settings.xml → <rubric_identifierref> → rubric title."""
    ident = resource.get("identifier", "")
    settings_path = extracted_dir / ident / "assignment_settings.xml"
    if not settings_path.exists():
        return ""
    root = ET.parse(settings_path).getroot()
    rubric_id = child_text(root, "rubric_identifierref")
    return rubrics.get(rubric_id, {}).get("title", "")


def get_discussion_rubric_ref(
    extracted_dir: Path, resource: dict, resources: dict, rubrics: dict
) -> str:
    """Read topicMeta dependency XML → <rubric_identifierref> → rubric title."""
    for dep_id in resource.get("dependencies", []):
        dep = resources.get(dep_id, {})
        dep_href = dep.get("href", "")
        if not dep_href:
            continue
        dep_path = extracted_dir / dep_href
        if not dep_path.exists():
            continue
        try:
            root = ET.parse(dep_path).getroot()
        except ET.ParseError:
            continue
        for el in root.iter():
            if local_name(el.tag) == "rubric_identifierref" and el.text:
                return rubrics.get(el.text.strip(), {}).get("title", "")
    return ""


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------

def get_assignment_html(extracted_dir: Path, resource: dict) -> str:
    """Return raw HTML for an assignment (from the resource folder)."""
    for rel in [resource.get("href", ""), *resource.get("files", [])]:
        if rel.lower().endswith(".html"):
            path = extracted_dir / rel
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
    return ""


def get_discussion_html(extracted_dir: Path, resource: dict) -> str:
    """Parse IMSCC discussion XML, unescape and return the HTML body."""
    for rel in [resource.get("href", ""), *resource.get("files", [])]:
        if rel.lower().endswith(".xml"):
            path = extracted_dir / rel
            if path.exists():
                try:
                    root = ET.parse(path).getroot()
                    encoded = child_text(root, "text")
                    return unescape(encoded) if encoded else ""
                except ET.ParseError:
                    pass
    return ""


def get_page_html(extracted_dir: Path, resource: dict) -> str:
    """Return raw HTML for a wiki page."""
    for rel in [resource.get("href", ""), *resource.get("files", [])]:
        if rel.lower().endswith(".html"):
            path = extracted_dir / rel
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
    return ""


# ---------------------------------------------------------------------------
# Syllabus extraction
# ---------------------------------------------------------------------------

def extract_syllabus(extracted_dir: Path, course_id: str, course_dir: Path) -> bool:
    """
    Read course_settings/syllabus.html, resolve the $IMS-CC-FILEBASE$ link to a
    .docx in web_resources/, extract its text with python-docx, and write
    {course_id}_syllabus.html into course_dir.
    Returns True if a docx was successfully extracted, False otherwise.
    """
    from urllib.parse import unquote

    syllabus_html_path = extracted_dir / "course_settings" / "syllabus.html"
    if not syllabus_html_path.exists():
        return False

    syl_html = syllabus_html_path.read_text(encoding="utf-8", errors="replace")

    # Find the $IMS-CC-FILEBASE$/... link pointing at a .docx
    m = re.search(r'\$IMS-CC-FILEBASE\$/([^"?]+\.docx)', syl_html, re.IGNORECASE)
    if m:
        rel_path = unescape(unquote(m.group(1)))  # URL-decode then HTML-unescape (&amp; → &)
        docx_path = extracted_dir / "web_resources" / rel_path
        if docx_path.exists():
            try:
                import docx as _docx
                doc = _docx.Document(str(docx_path))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                text = "\n".join(paragraphs)
                header = (
                    f"<!-- CONTENT-TYPE: Syllabus -->\n"
                    f"<!-- COURSE: {course_id} -->\n"
                    f"<!-- TITLE: Course Syllabus -->"
                )
                out_path = course_dir / f"{course_id}_syllabus.html"
                out_path.write_text(f"{header}\n\n<pre>{text}</pre>", encoding="utf-8")
                return True
            except Exception:
                pass

    # Fallback: write the raw syllabus.html (link only, better than nothing)
    header = (
        f"<!-- CONTENT-TYPE: Syllabus -->\n"
        f"<!-- COURSE: {course_id} -->\n"
        f"<!-- TITLE: Course Syllabus -->"
    )
    out_path = course_dir / f"{course_id}_syllabus.html"
    out_path.write_text(f"{header}\n\n{syl_html}", encoding="utf-8")
    return False


# ---------------------------------------------------------------------------
# Write canvas_courses output
# ---------------------------------------------------------------------------

def write_course_files(
    course_id: str,
    course_dir: Path,
    module_items: list[dict],
    resources: dict,
    rubrics: dict,
    extracted_dir: Path,
    course_title: str,
) -> dict:
    """Write CQR-compatible HTML files to canvas_courses/{course_id}/. Returns counts."""
    # Clear existing HTML files and the extraction log so no Cowork artifacts linger
    if course_dir.exists():
        for old_file in course_dir.glob("*.html"):
            old_file.unlink()
        log_file = course_dir / f"{course_id}_extraction-log.json"
        if log_file.exists():
            log_file.unlink()
    course_dir.mkdir(parents=True, exist_ok=True)

    counts = {"assignments": 0, "discussions": 0, "pages": 0, "rubrics": 0, "skipped": 0}
    included_items: list[tuple[str, str]] = []   # (type_label, title)
    ignored_items: list[tuple[str, str]] = []    # (title, reason)

    for item in module_items:
        content_type = item["contentType"]
        title = item["title"]
        module_title = item["moduleTitle"]
        resource = resources.get(item["identifierref"], {})

        if content_type == "Assignment":
            rubric_ref = get_assignment_rubric_ref(extracted_dir, resource, rubrics)
            html = get_assignment_html(extracted_dir, resource)
            header = (
                f"<!-- CONTENT-TYPE: Assignment -->\n"
                f"<!-- COURSE: {course_id} -->\n"
                f"<!-- MODULE: {module_title} -->\n"
                f"<!-- TITLE: {title} -->"
            )
            if rubric_ref:
                header += f"\n<!-- RUBRIC-REF: {rubric_ref} -->"
            filename = f"{course_id}_assignment_{slugify(title)}.html"
            (course_dir / filename).write_text(f"{header}\n\n{html}", encoding="utf-8")
            counts["assignments"] += 1
            included_items.append(("Assignment", title))

        elif content_type == "DiscussionTopic":
            if is_excluded_page(title):
                counts["skipped"] += 1
                ignored_items.append((title, "excluded title"))
                continue
            rubric_ref = get_discussion_rubric_ref(extracted_dir, resource, resources, rubrics)
            html = get_discussion_html(extracted_dir, resource)
            header = (
                f"<!-- CONTENT-TYPE: Discussion -->\n"
                f"<!-- COURSE: {course_id} -->\n"
                f"<!-- MODULE: {module_title} -->\n"
                f"<!-- TITLE: {title} -->"
            )
            if rubric_ref:
                header += f"\n<!-- RUBRIC-REF: {rubric_ref} -->"
            filename = f"{course_id}_discussion_{slugify(title)}.html"
            (course_dir / filename).write_text(f"{header}\n\n{html}", encoding="utf-8")
            counts["discussions"] += 1
            included_items.append(("Discussion", title))

        elif content_type == "WikiPage":
            if is_excluded_page(title):
                counts["skipped"] += 1
                ignored_items.append((title, "excluded title"))
                continue
            html = get_page_html(extracted_dir, resource)
            header = (
                f"<!-- CONTENT-TYPE: Page -->\n"
                f"<!-- COURSE: {course_id} -->\n"
                f"<!-- MODULE: {module_title} -->\n"
                f"<!-- TITLE: {title} -->"
            )
            filename = f"{course_id}_page_{slugify(title)}.html"
            (course_dir / filename).write_text(f"{header}\n\n{html}", encoding="utf-8")
            counts["pages"] += 1
            included_items.append(("Page", title))

        else:
            counts["skipped"] += 1
            ignored_items.append((title, content_type or "unsupported type"))

    # Rubrics from rubrics.xml — one file per rubric
    for rubric in rubrics.values():
        title = rubric["title"]
        header = (
            f"<!-- CONTENT-TYPE: Rubric -->\n"
            f"<!-- COURSE: {course_id} -->\n"
            f"<!-- TITLE: {title} -->\n"
            f"<!-- RUBRIC-NAME: {title} -->"
        )
        filename = f"{course_id}_rubric_{slugify(title)}.html"
        (course_dir / filename).write_text(f"{header}\n\n{rubric['xml']}", encoding="utf-8")
        counts["rubrics"] += 1
        included_items.append(("Rubric", title))

    # Syllabus — extract from course_settings/syllabus.html + linked .docx
    counts["syllabus"] = 0
    syl_extracted = extract_syllabus(extracted_dir, course_id, course_dir)
    if (course_dir / f"{course_id}_syllabus.html").exists():
        counts["syllabus"] = 1
        label = "Syllabus (from .docx)" if syl_extracted else "Syllabus (link only)"
        included_items.append((label, "Course Syllabus"))

    extracted_at = datetime.now(timezone.utc).isoformat()
    total_files = sum(counts[k] for k in ("assignments", "discussions", "pages", "rubrics", "syllabus"))

    # Extraction log (read by sync.py for course title discovery)
    log = {
        "course_id": course_id,
        "course_title": course_title,
        "extracted_at": extracted_at,
        "file_count": total_files,
    }
    (course_dir / f"{course_id}_extraction-log.json").write_text(
        json.dumps(log, indent=2), encoding="utf-8"
    )

    # Extraction report (human-readable audit trail)
    sep = "=" * 70
    lines = [
        f"{course_id} Extraction Report",
        sep,
        f"Course title: {course_title or '(not detected)'}",
        f"Extracted at: {extracted_at}",
        f"Source: .imscc (ingest_imscc.py)",
        "",
        f"Total module items found: {len(module_items)}",
        "",
        f"EXTRACTED ({total_files} files):",
    ]
    for type_label, title in included_items:
        lines.append(f"  - {type_label}: {title}")
    lines += [
        "",
        f"IGNORED ({len(ignored_items)} items):",
    ]
    for title, reason in ignored_items:
        lines.append(f"  - {title}  ({reason})")
    lines += [
        "",
        sep,
    ]
    (course_dir / f"{course_id}_extraction-report.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    return counts


# ---------------------------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------------------------

def ingest_imscc(
    imscc_path: Path,
    course_id: str | None = None,
    dest_dir: Path | None = None,
) -> dict:
    """
    Full pipeline: extract .imscc → write HTML files → optionally ingest to SQLite.

    If dest_dir is provided, files are written directly there and SQLite ingestion
    is skipped (CQR path). Otherwise files go to canvas_courses/{course_id}/ and
    SQLite is updated (PII path).

    Returns summary dict with course_id, course_title, file counts, and db counts
    (db counts are zero when dest_dir is provided).
    """
    if not imscc_path.exists():
        raise FileNotFoundError(f"File not found: {imscc_path}")

    course_id = course_id or course_id_from_filename(imscc_path.name)

    with tempfile.TemporaryDirectory() as tmpdir:
        extracted_dir = Path(tmpdir) / "extracted"
        extracted_dir.mkdir()

        try:
            with zipfile.ZipFile(imscc_path) as zf:
                safe_extract(zf, extracted_dir)
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Not a valid ZIP/IMSCC file: {exc}") from exc

        manifest_path = extracted_dir / "imsmanifest.xml"
        module_meta_path = extracted_dir / "course_settings" / "module_meta.xml"
        rubrics_xml_path = extracted_dir / "course_settings" / "rubrics.xml"

        if not manifest_path.exists():
            raise FileNotFoundError("imsmanifest.xml not found — not a valid Canvas export")
        if not module_meta_path.exists():
            raise FileNotFoundError("course_settings/module_meta.xml not found")

        resources = parse_manifest_resources(manifest_path)
        module_items = parse_module_items(module_meta_path)
        rubrics = parse_rubrics(rubrics_xml_path)
        course_title = detect_course_title(manifest_path, course_id)

        course_dir = dest_dir if dest_dir is not None else COURSES_DIR / course_id
        file_counts = write_course_files(
            course_id, course_dir, module_items, resources, rubrics, extracted_dir, course_title
        )

    # CQR path: skip SQLite ingestion
    if dest_dir is not None:
        return {
            "course_id": course_id,
            "course_title": course_title,
            "files_written": file_counts,
            "db_ingested": {},
        }

    # PII path: ingest into SQLite via sync.py's pipeline
    from sync import (
        ensure_ingest_log_table, ensure_course_registered, save_competency_links,
        delete_course_data, restore_competency_links, set_fingerprint, compute_fingerprint,
    )
    from ingest import ingest_one_course

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_ingest_log_table(conn)
    ensure_course_registered(conn, course_id, course_dir)
    saved_links = save_competency_links(conn, course_id)
    delete_course_data(conn, course_id)
    db_counts = ingest_one_course(conn, course_id, course_dir)
    restore_competency_links(conn, course_id, saved_links)
    fp = compute_fingerprint(course_dir)
    set_fingerprint(conn, course_id, fp)
    conn.close()

    return {
        "course_id": course_id,
        "course_title": course_title,
        "files_written": file_counts,
        "db_ingested": db_counts,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ingest a Canvas .imscc export into the CQR database."
    )
    parser.add_argument("imscc_file", help="Path to the .imscc export file")
    parser.add_argument("--course-id", help="Override detected course ID (e.g. PM-810)")
    args = parser.parse_args()

    result = ingest_imscc(Path(args.imscc_file).expanduser().resolve(), args.course_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
