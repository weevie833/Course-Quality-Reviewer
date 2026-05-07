"""
Ingest AI-in-Education knowledge articles into the knowledge_articles table.

Source: /Users/stevecovello/Desktop/Claude Projects/_Program Intelligence Interface/Specialized knowledge/AI in Education/

Run this once (or re-run to refresh):
    python3 ingest_ai_knowledge.py
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "program.db"

AI_KNOWLEDGE_DIR = Path(
    "/Users/stevecovello/Desktop/Claude Projects/"
    "_Program Intelligence Interface/Specialized knowledge/AI in Education"
)

DOMAIN = "ai_in_education"


def extract_title(text: str, filename: str) -> str:
    """Pull first H1 from markdown; fall back to cleaned filename."""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    name = filename.replace(".md", "").replace(".pdf", "")
    name = re.sub(r"[-_]+", " ", name)
    return name.strip().title()


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            domain      TEXT NOT NULL,
            title       TEXT NOT NULL,
            body_text   TEXT NOT NULL,
            source_file TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ka_domain ON knowledge_articles(domain)")
    conn.commit()


def ingest(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM knowledge_articles WHERE domain = ?", (DOMAIN,))

    files = sorted(AI_KNOWLEDGE_DIR.glob("*.md"))
    inserted = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        title = extract_title(text, f.name)
        conn.execute(
            "INSERT INTO knowledge_articles (domain, title, body_text, source_file) VALUES (?, ?, ?, ?)",
            (DOMAIN, title, text, f.name),
        )
        inserted += 1

    conn.commit()
    print(f"Ingested {inserted} articles into knowledge_articles (domain={DOMAIN})")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)
    ingest(conn)
    conn.close()
