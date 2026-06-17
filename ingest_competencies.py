"""
Populates competency tables in program.db from the MSLD competency rubric PDFs.
Clears and rebuilds competency data on each run.
Run: python3 ingest_competencies.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "program.db"

# ---------------------------------------------------------------------------
# Categories (letter-based: A = Individual, B = Interpersonal/Organizational)
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("A", "Individual Leadership Competencies"),
    ("B", "Interpersonal & Organizational Competencies"),
]

# ---------------------------------------------------------------------------
# Competencies: (category_letter, code, name, short_description)
# ---------------------------------------------------------------------------
COMPETENCIES = [
    ("A", "LD-1.1.1", "Communication: Effective Writing and Listening",
     "Demonstrate strong listening and communication skills"),
    ("A", "LD-1.2.1", "Self Awareness: Knows Own Values",
     "Has identified their personal values and sees the relationship of values to leadership"),
    ("A", "LD-1.2.2", "Self Awareness: Resilience",
     "Demonstrates resiliency"),
    ("A", "LD-1.2.3", "Self Awareness: Invites Feedback",
     "Seek Feedback"),
    ("A", "LD-1.2.4", "Self Awareness: Demonstrates Ethical Behavior",
     "Behaves ethically"),
    ("A", "LD-1.2.5", "Self Awareness: Introspection",
     "Has the capacity for introspection"),
    ("A", "LD-1.2.6", "Self Awareness: Reflective",
     "Personal and collective reflection"),
    ("A", "LD-1.3.1", "Creative and Innovation: Problem Solving",
     "Identifies and evaluates solutions to situations"),
    ("B", "LD-2.1.1", "Organizational Awareness: Political Skills",
     "Understands political awareness"),
    ("B", "LD-2.1.2", "Organizational Awareness: Establish-Share Vision",
     "Collaborates visioning process"),
    ("B", "LD-2.2.1", "Change: Appropriate Risk Taking",
     "Avoids unnecessary risks"),
    ("B", "LD-2.3.1", "Relationship Management: Values Others",
     "Honors and respects others"),
    ("B", "LD-2.3.2", "Relationship Management: Team Building",
     "Facilitates team skill building"),
    ("B", "LD-2.3.3", "Relationship Management: Motivates",
     "Relationship Management: Motivates"),
    ("B", "LD-2.3.4", "Relationship Management: Mentors and Coaches",
     "Guides and coaches others"),
    ("B", "LD-2.4.1", "Conflict Management: Effective",
     "Works effectively through conflict"),
    ("B", "LD-2.5.1", "Strategic Management: Change Management",
     "Integrates and leads change"),
    ("B", "LD-2.6.1", "Diversity: Culture of Inclusion",
     "Creates inclusiveness"),
    ("B", "LD-2.6.2", "Diversity: Values Diversity",
     "Understands diversity"),
]

# ---------------------------------------------------------------------------
# Level descriptors: (code, level, descriptor)
# Source PDFs noted where LD820 had copy-paste template errors and another
# PDF's correct descriptors were used instead.
# ---------------------------------------------------------------------------
LEVEL_DESCRIPTORS = [
    # LD-1.1.1 — all PDFs consistent
    ("LD-1.1.1", 1, "Identifies examples of listening and communication skills. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.1.1", 2, "Recognizes examples of listening and communication skills and ways to approach solutions or possibilities in presenting information that is analytical and factual, but follows a formulaic approach and does not take context into account. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.1.1", 3, "Applies strong listening and communication skills that account for contextual features and allow for variability across contexts. Applies the competency with assistance."),
    ("LD-1.1.1", 4, "Effectively varies strong listening and communication skills on the basis of knowledge and experience across contexts. Applies the competency with little or no assistance."),
    ("LD-1.1.1", 5, "Effectively varies strong listening and communication skills as a matter of habit and demonstrates commitment to evaluating approaches across contexts. Serves as a key resource and advises others."),

    # LD-1.2.1 — use LD850 (LD820 had template copy-paste error showing A.11 descriptors)
    ("LD-1.2.1", 1, "Has identified their personal values and seeks feedback to practice their values at work. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.1", 2, "Has identified their personal values and seeks to practice their values at work. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.1", 3, "Has identified their personal values and allows their values to become part of their work. Applies the competency with assistance."),
    ("LD-1.2.1", 4, "Has identified their personal values and assists others to practice their values. Applies the competency with little or no assistance."),
    ("LD-1.2.1", 5, "Acts congruently with their own values. Serves as a key resource for others."),

    # LD-1.2.2 — use LD810 (LD820 had template copy-paste error)
    ("LD-1.2.2", 1, "Lacks the ability to tolerate and rebound from difficult situations. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.2", 2, "Demonstrates limited ability to tolerate and rebound from difficult situations. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.2", 3, "Demonstrates the ability to tolerate and rebound from difficult situations. Applies the competency with assistance."),
    ("LD-1.2.2", 4, "Demonstrates the ability to tolerate and rebound from considerably difficult situations. Applies the competency with little or no assistance."),
    ("LD-1.2.2", 5, "Demonstrates the ability to tolerate and rebound from extremely difficult situations. Serves as a key resource for others."),

    # LD-1.2.3 — use COM800/LD850 (LD820 had template copy-paste error)
    ("LD-1.2.3", 1, "Recognizes the personal need for change and requests advice from peers and supervisors. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.3", 2, "Recognizes the personal need for change and feedback to implement changes. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.3", 3, "Recognizes the personal need for change and requests help to implement changes. Applies the competency with assistance."),
    ("LD-1.2.3", 4, "Recognizes the personal need for change and requests help to implement changes. Applies the competency with little or no assistance."),
    ("LD-1.2.3", 5, "Recognizes the personal need for change and helps others implement change. Serves as a key resource for others."),

    # LD-1.2.4 — consistent across all PDFs
    ("LD-1.2.4", 1, "Reflects on one's current reputation in personal, educational, professional, and online settings. Appreciate how the perceptions of others are important. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.4", 2, "Considers what one wants to be known for in personal, education, professional and online setting. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.4", 3, "Exhibits a commitment to ethics by walking the talk. Seeks feedback from others to guide decisions and actions in personal and professional setting. Applies the competency with assistance."),
    ("LD-1.2.4", 4, "Develops knowledge, skills, and attitudes that lead to making a positive impression in every facet of life. Applies the competency with little or no assistance."),
    ("LD-1.2.4", 5, "Supports others as they attempt to achieve congruence between their intended and perceived reputations. Serves as a key resource for others."),

    # LD-1.2.5 — use LD821/LD850 (LD820 had template copy-paste error)
    ("LD-1.2.5", 1, "Recognizes gaps in one's own skills and takes advantage of opportunities to improve. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.5", 2, "Balances personal strengths and weaknesses and weaknesses of others. Implements techniques for dealing with stress and managing day to day work. Manages one's own emotions. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.5", 3, "Understands how others perceive their actions, comments, and tones. Applies the competency with assistance."),
    ("LD-1.2.5", 4, "Calms self and others; positively impacts others during times of stress. Uses setbacks in a constructive way. Comfortably handles risk and uncertainty. Applies the competency with little or no assistance."),
    ("LD-1.2.5", 5, "Views challenges as opportunities for growth. Uses understanding of self and others to reach out to others and foster positive relationships. Serves as a key resource for others."),

    # LD-1.2.6 — LD810 Communication / LD850
    ("LD-1.2.6", 1, "Reviews effectiveness of personal and collective practice. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.2.6", 2, "Reviews effectiveness of personal and collective practice and contemplates change. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.2.6", 3, "Reviews effectiveness of personal and collective practice and suggests change. Applies the competency with assistance."),
    ("LD-1.2.6", 4, "Reviews effectiveness of personal and collective practice and implements personal change. Applies the competency with little or no assistance."),
    ("LD-1.2.6", 5, "Reviews effectiveness of personal and collective practice and mentors others through change. Serves as a key resource for others."),

    # LD-1.3.1 — consistent across all PDFs
    ("LD-1.3.1", 1, "Identifies and evaluates strategies and solutions. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-1.3.1", 2, "Develops plans of action to weigh differing strategies and solutions. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-1.3.1", 3, "Reconciles conflicting and/or incomplete information to develop solutions. Applies the competency with assistance."),
    ("LD-1.3.1", 4, "Synthesizes information to develop an action plan. Applies the competency with little or no assistance."),
    ("LD-1.3.1", 5, "Aptly problem solves and implements plans across all levels of the agency. Serves as a key resource for others."),

    # LD-2.1.1 — consistent across all PDFs
    ("LD-2.1.1", 1, "Considers implications of actions before engaging in dialog or considering change. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.1.1", 2, "Addresses stakeholders and develops relationships with those stakeholders. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.1.1", 3, "Evaluates political implications by considering different courses of action on a key issue. Applies the competency with assistance."),
    ("LD-2.1.1", 4, "Addresses controversial political issues by conducting research and considering best practices. Applies the competency with little or no assistance."),
    ("LD-2.1.1", 5, "Considers the political implication before implementing any action. Serves as a key resource for others."),

    # LD-2.1.2 — consistent across all PDFs
    ("LD-2.1.2", 1, "Understands the mission and vision of the organization. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.1.2", 2, "Models organizational mission and values to others. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.1.2", 3, "Anticipates and seizes new opportunities that are aligned with the mission and goals of the organization. Inspires others to see the opportunity. Applies the competency with assistance."),
    ("LD-2.1.2", 4, "Anticipates and seizes new opportunities that are aligned with the mission and goals of the organization. Inspires others to see and participate in the opportunity. Applies the competency with little or no assistance."),
    ("LD-2.1.2", 5, "Manages change by seeking to understand its effects upon the organization and key stakeholders, by guiding others through change, and by addressing resistance to that change. Serves as a key resource for others."),

    # LD-2.2.1 — LD810 Communication / LD850
    ("LD-2.2.1", 1, "Evaluates liabilities before making a decision or taking action. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.2.1", 2, "Thoughtfully evaluates liabilities before making a decision or taking action. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.2.1", 3, "Thoughtfully evaluates liabilities before making a decision or taking action and takes action to mitigate risks. Applies the competency with assistance."),
    ("LD-2.2.1", 4, "Weighs the liabilities with the benefits before making a decision or taking action and takes action to mitigate risks. Applies the competency with little or no assistance."),
    ("LD-2.2.1", 5, "Assists others to weigh the liabilities with the benefits before they make a decision. Assists others as they develop a plan to mitigate the risks. Serves as a key resource for others."),

    # LD-2.3.1 — use LD804/LD810 (LD820 5.0 had a copy-paste error repeating level 4)
    ("LD-2.3.1", 1, "Works collaboratively with colleagues. Respects other's time. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.3.1", 2, "Actively contributes to teams and organization-wide initiatives. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.3.1", 3, "Solicits input and genuinely values others' ideas and expertise; is willing to learn from others. Applies the competency with assistance."),
    ("LD-2.3.1", 4, "Supports and acts in accordance with final group decision, even when such decisions may not entirely reflect own position. Applies the competency with little or no assistance."),
    ("LD-2.3.1", 5, "Respects and implements decisions and activities as requested, even if his or her own personal opinion about their value might differ. Serves as a key resource for others."),

    # LD-2.3.2 — consistent across all PDFs
    ("LD-2.3.2", 1, "Uses team building exercises to improve group dynamics. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.3.2", 2, "Forms teams to identify and address agency concerns. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.3.2", 3, "Includes the entire team in decision-making process. Leads team members from various organizational units to create new systems or processes. Applies the competency with assistance."),
    ("LD-2.3.2", 4, "Promotes cohesiveness of team by assigning roles and establishing overall objectives. Applies the competency with little or no assistance."),
    ("LD-2.3.2", 5, "Inspires teams to accomplish long-term strategic goals. Serves as a key resource for others."),

    # LD-2.3.3 — consistent across all PDFs
    ("LD-2.3.3", 1, "Understands basic motivational model. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.3.3", 2, "Identifies models that are appropriate for differing individuals. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.3.3", 3, "Finds and implements creative ways to make people's work rewarding based on their motivating factors. Identifies and promptly tackles morale problems. Applies the competency with assistance."),
    ("LD-2.3.3", 4, "Recognizes and rewards people for their achievements. Applies the competency with little or no assistance."),
    ("LD-2.3.3", 5, "Signals own commitment to a process by being personally present and involved at key events. Gives talks or presentations that energize groups. Serves as a key resource for others."),

    # LD-2.3.4 — consistent across all PDFs
    ("LD-2.3.4", 1, "Provides helpful advice to others. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.3.4", 2, "Shares information, advice and suggestions to help others be more successful. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.3.4", 3, "Gives people assignments to help develop their abilities. Expresses confidence in other's ability to be successful. Applies the competency with assistance."),
    ("LD-2.3.4", 4, "Regularly meets with people to review their progress. Recognizes and reinforces people's efforts and improvements. Applies the competency with little or no assistance."),
    ("LD-2.3.4", 5, "Helps others to grow their skills and abilities to develop others. Serves as a key resource for others."),

    # LD-2.4.1 — consistent across all PDFs
    ("LD-2.4.1", 1, "Identifies situations needing attention and steps in. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.4.1", 2, "Implements changes to ensure the environment is fair and equitable. Ensures employees receive mediation. Resolves issues by meeting one on one with team members. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.4.1", 3, "Meets with people and addresses concerns in response to critical issues in an open and honest manner. Takes actions to address behavior issues. Resolves conflict using mediation techniques. Applies the competency with assistance."),
    ("LD-2.4.1", 4, "Recognizes conflict and takes steps to address issues by meeting with the involved parties. Applies the competency with little or no assistance."),
    ("LD-2.4.1", 5, "Leads managers through consensus process on agency's response to controversial issues. Serves as a key resource for others."),

    # LD-2.5.1 — use LD810 version
    ("LD-2.5.1", 1, "Recognizes the need to develop a strategy to lead change. Needs close supervision to implement changes. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.5.1", 2, "Demonstrates the ability to lead change and requires frequent feedback to implement change. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.5.1", 3, "Demonstrates the ability to lead change and requires occasional feedback to implement change. Applies the competency with assistance."),
    ("LD-2.5.1", 4, "Demonstrates the ability to lead change and requires little to no feedback to implement change. Integrates and leads change."),
    ("LD-2.5.1", 5, "Demonstrates the ability to lead change and acts as a resource to those implementing change."),

    # LD-2.6.1 — consistent across all PDFs
    ("LD-2.6.1", 1, "Recognizes that people will judge one another due to unconscious bias. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.6.1", 2, "Learns about their bias and creates transparent, consistent decision-making processes around talent. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.6.1", 3, "Seeks opportunities to experience cultural diversity environments. Implements transparent, consistent decision-making processes around talent. Applies the competency with assistance."),
    ("LD-2.6.1", 4, "Uses appropriate verbal and nonverbal behavior in cross-culture encounters. Confident leading cross-cultural teams. Changes style appropriate with cross-cultural encounters. Applies the competency with little or no assistance."),
    ("LD-2.6.1", 5, "Creates a diverse and inclusive environment. Identifies creative approaches for targeted recruiting to develop a diverse workforce that benefits diverse strengths. Serves as a key resource for others."),

    # LD-2.6.2 — consistent across all PDFs
    ("LD-2.6.2", 1, "Treats all team members with fairness and respect and values the uniqueness of each team person. Recognizes the skill or the ability in others without demonstrating it themselves."),
    ("LD-2.6.2", 2, "Clearly and authentically articulates the value of diversity and inclusion. Applies the competency in specific ways, requires a high level of assistance."),
    ("LD-2.6.2", 3, "Takes personal responsibility for diversity and inclusion agency outcomes. Applies the competency with assistance."),
    ("LD-2.6.2", 4, "Allocates resources towards improving diversity and inclusion. Applies the competency with little or no assistance."),
    ("LD-2.6.2", 5, "Challenges entrenched organizational attitudes and practices that promote homogeneity. Serves as a key resource for others."),
]

# ---------------------------------------------------------------------------
# Assignment-to-competency mapping derived from PDF filenames.
# Format: (course_id, title_keywords, [competency_codes])
# title_keywords: space-separated words used for fuzzy LIKE matching
# ---------------------------------------------------------------------------
ITEM_ASSIGNMENTS = [
    ("LD-804",  "Organizational Plan, Team Charter (Leadership Students Only)", ["LD-1.2.4", "LD-1.3.1", "LD-2.1.1", "LD-2.1.2", "LD-2.3.1", "LD-2.3.2", "LD-2.3.3", "LD-2.3.4"]),
    ("LD-820",  "Leadership Action Plan (Leadership and Nonprofit Students)", ["LD-1.1.1", "LD-1.2.1", "LD-1.2.2", "LD-1.2.3", "LD-1.2.5", "LD-2.3.1"]),
    ("LD-821",  "Ethical Leadership",               ["LD-1.2.4", "LD-1.2.5", "LD-2.3.4", "LD-2.6.1", "LD-2.6.2"]),
    ("COM-800", "Application",                      ["LD-1.1.1", "LD-1.2.3", "LD-2.1.1", "LD-2.1.2", "LD-2.4.1", "LD-2.5.1"]),
    ("LD-823",  "Value of Diversity",               ["LD-1.1.1", "LD-2.1.1", "LD-2.1.2", "LD-2.3.1", "LD-2.3.2", "LD-2.6.1", "LD-2.6.2"]),
    ("LD-823",  "Identifying Desired Future States",["LD-1.1.1", "LD-2.1.2"]),
    ("LD-810",  "Change Management Plan",           ["LD-1.1.1", "LD-1.2.2", "LD-1.2.3", "LD-1.3.1", "LD-2.1.1", "LD-2.1.2", "LD-2.3.1", "LD-2.3.3", "LD-2.4.1", "LD-2.5.1"]),
    ("LD-810",  "Communication Management Plan",    ["LD-1.1.1", "LD-1.2.2", "LD-1.2.6", "LD-2.2.1", "LD-1.3.1", "LD-2.4.1", "LD-2.5.1", "LD-2.6.1", "LD-2.6.2"]),
    ("LD-850",  "Leadership Reflection Paper",      ["LD-1.1.1", "LD-1.2.1", "LD-1.2.3", "LD-1.2.4", "LD-1.2.5", "LD-1.2.6", "LD-2.2.1", "LD-2.3.3"]),
]


def fuzzy_find_item(conn, course_id: str, keywords: str) -> dict | None:
    """Find the best-matching course item using keyword fragments."""
    words = [w for w in keywords.replace("_", " ").split() if len(w) > 3]
    best = None
    best_score = 0
    rows = conn.execute(
        "SELECT id, title FROM course_items WHERE course_id = ? AND content_type IN ('Assignment','Discussion')",
        (course_id,)
    ).fetchall()
    for row in rows:
        title_lower = row["title"].lower()
        score = sum(1 for w in words if w.lower() in title_lower)
        if score > best_score:
            best_score = score
            best = row
    return dict(best) if best and best_score > 0 else None


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")

    # Create competency tables if they don't exist yet (first run)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS competency_categories (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            letter TEXT NOT NULL UNIQUE,
            title  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS competencies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES competency_categories(id),
            code        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS competency_level_descriptors (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            competency_id INTEGER NOT NULL REFERENCES competencies(id),
            level         INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
            descriptor    TEXT NOT NULL,
            UNIQUE(competency_id, level)
        );

        CREATE TABLE IF NOT EXISTS item_competency_links (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id       INTEGER NOT NULL REFERENCES course_items(id),
            competency_id INTEGER NOT NULL REFERENCES competencies(id),
            UNIQUE(item_id, competency_id)
        );
    """)

    # Remove only this script's own category data (LD's A/B), leave PM/SHRM intact
    ld_letters = [letter for letter, _ in CATEGORIES]
    placeholders = ",".join("?" * len(ld_letters))
    existing_cat_ids = [
        r["id"] for r in conn.execute(
            f"SELECT id FROM competency_categories WHERE letter IN ({placeholders})", ld_letters
        ).fetchall()
    ]
    if existing_cat_ids:
        cat_placeholders = ",".join("?" * len(existing_cat_ids))
        existing_comp_ids = [
            r["id"] for r in conn.execute(
                f"SELECT id FROM competencies WHERE category_id IN ({cat_placeholders})", existing_cat_ids
            ).fetchall()
        ]
        if existing_comp_ids:
            comp_placeholders = ",".join("?" * len(existing_comp_ids))
            conn.execute(f"DELETE FROM item_competency_links WHERE competency_id IN ({comp_placeholders})", existing_comp_ids)
            conn.execute(f"DELETE FROM competency_level_descriptors WHERE competency_id IN ({comp_placeholders})", existing_comp_ids)
            conn.execute(f"DELETE FROM competencies WHERE id IN ({comp_placeholders})", existing_comp_ids)
        conn.execute(f"DELETE FROM competency_categories WHERE id IN ({cat_placeholders})", existing_cat_ids)

    # Insert categories
    for letter, title in CATEGORIES:
        conn.execute(
            "INSERT INTO competency_categories (letter, title) VALUES (?, ?)",
            (letter, title)
        )

    # Insert competencies
    for cat_letter, code, name, description in COMPETENCIES:
        cat_id = conn.execute(
            "SELECT id FROM competency_categories WHERE letter = ?", (cat_letter,)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO competencies (category_id, code, name, description) VALUES (?, ?, ?, ?)",
            (cat_id, code, name, description)
        )

    # Insert level descriptors
    for code, level, descriptor in LEVEL_DESCRIPTORS:
        comp_id = conn.execute(
            "SELECT id FROM competencies WHERE code = ?", (code,)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO competency_level_descriptors (competency_id, level, descriptor) VALUES (?, ?, ?)",
            (comp_id, level, descriptor)
        )

    conn.commit()

    # Fuzzy-match assignments and populate item_competency_links
    print("\nMatching assignments to competencies:")
    unmatched = []
    matched_count = 0

    for course_id, keywords, codes in ITEM_ASSIGNMENTS:
        item = fuzzy_find_item(conn, course_id, keywords)
        if not item:
            unmatched.append((course_id, keywords))
            print(f"  [NO MATCH] {course_id} — '{keywords}'")
            continue

        print(f"  [MATCH] {course_id} — '{keywords}' → '{item['title']}'")
        for code in codes:
            comp = conn.execute(
                "SELECT id FROM competencies WHERE code = ?", (code,)
            ).fetchone()
            if not comp:
                print(f"    [WARN] competency code {code} not found")
                continue
            conn.execute(
                "INSERT OR IGNORE INTO item_competency_links (item_id, competency_id) VALUES (?, ?)",
                (item["id"], comp["id"])
            )
            matched_count += 1

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    # Summary
    cats   = conn.execute("SELECT COUNT(*) FROM competency_categories").fetchone()[0]
    comps  = conn.execute("SELECT COUNT(*) FROM competencies").fetchone()[0]
    descs  = conn.execute("SELECT COUNT(*) FROM competency_level_descriptors").fetchone()[0]
    links  = conn.execute("SELECT COUNT(*) FROM item_competency_links").fetchone()[0]
    conn.close()

    print(f"\nDone.")
    print(f"  {cats} categories, {comps} competencies, {descs} level descriptors")
    print(f"  {links} item-competency links across {len(ITEM_ASSIGNMENTS) - len(unmatched)} assignments")
    if unmatched:
        print(f"\nUnmatched assignments requiring manual review:")
        for course_id, keywords in unmatched:
            print(f"  {course_id} — '{keywords}'")


if __name__ == "__main__":
    run()
