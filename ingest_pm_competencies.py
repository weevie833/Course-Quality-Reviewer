"""
Ingests PMI Project Management Competencies 3.0 into the database.

Structure:
  - 2 competency categories (Process / People)
  - 90 sub-competencies (leaf-level, the items that get assessed)
  - item_competency_links mapped directly by DB item ID

Safe to re-run: drops and recreates only PM competency data.
Does NOT touch existing LD competency categories/competencies/links.
"""

import sqlite3

DB_PATH = "data/program.db"

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("P", "Project Management Processes"),   # covers 1.x competencies
    ("L", "People & Leadership"),             # covers 2.x competencies
]

# ---------------------------------------------------------------------------
# Competencies  (category_letter, code, name)
# ---------------------------------------------------------------------------
COMPETENCIES = [
    # --- Domain 1: Project Management Processes ---
    ("P", "PM-1.01.1", "Assess opportunities to deliver value incrementally"),
    ("P", "PM-1.01.2", "Examine the business value throughout the project"),
    ("P", "PM-1.01.3", "Support the team to subdivide project tasks as necessary to find the minimum viable product"),
    ("P", "PM-1.02.1", "Analyze communication needs of all stakeholders"),
    ("P", "PM-1.02.2", "Determine communication methods, channels, frequency, and level of detail for all stakeholders"),
    ("P", "PM-1.02.3", "Communicate project information and updates effectively"),
    ("P", "PM-1.02.4", "Confirm communication is understood and feedback is received"),
    ("P", "PM-1.03.1", "Determine risk management options"),
    ("P", "PM-1.03.2", "Iteratively assess and prioritize risks"),
    ("P", "PM-1.04.1", "Analyze stakeholders (e.g., power interest grid, influence, impact)"),
    ("P", "PM-1.04.2", "Categorize stakeholders"),
    ("P", "PM-1.04.3", "Engage stakeholders by category"),
    ("P", "PM-1.04.4", "Develop, execute, and validate a strategy for stakeholder engagement"),
    ("P", "PM-1.05.1", "Estimate budgetary needs based on the scope of the project and lessons learned from past projects"),
    ("P", "PM-1.05.2", "Anticipate future budget challenges"),
    ("P", "PM-1.05.3", "Monitor budget variations and work with governance process to adjust as necessary"),
    ("P", "PM-1.05.4", "Plan and manage resources"),
    ("P", "PM-1.06.1", "Estimate project tasks (milestones, dependencies, story points)"),
    ("P", "PM-1.06.2", "Utilize benchmarks and historical data"),
    ("P", "PM-1.06.3", "Prepare schedule based on methodology"),
    ("P", "PM-1.06.4", "Measure ongoing progress based on methodology"),
    ("P", "PM-1.06.5", "Modify schedule, as needed, based on methodology"),
    ("P", "PM-1.06.6", "Coordinate with other projects and other operations"),
    ("P", "PM-1.07.1", "Determine quality standard required for project deliverables"),
    ("P", "PM-1.07.2", "Recommend options for improvement based on quality gaps"),
    ("P", "PM-1.07.3", "Continually survey project deliverable quality"),
    ("P", "PM-1.08.1", "Develop a project charter in concert with project sponsor"),
    ("P", "PM-1.08.2", "Determine and prioritize requirements"),
    ("P", "PM-1.08.3", "Break down scope (e.g., Work Breakdown Structure, backlog)"),
    ("P", "PM-1.08.4", "Monitor and validate scope"),
    ("P", "PM-1.09.1", "Consolidate the project/phase plans"),
    ("P", "PM-1.09.2", "Assess consolidated project plans for dependencies, gaps, and continued business value"),
    ("P", "PM-1.09.3", "Analyze the data collected"),
    ("P", "PM-1.09.4", "Collect and analyze data to make informed project decisions"),
    ("P", "PM-1.09.5", "Determine critical information requirements"),
    ("P", "PM-1.10.1", "Anticipate and embrace the need for change (e.g., follow change management practices)"),
    ("P", "PM-1.10.2", "Determine strategy to handle change"),
    ("P", "PM-1.10.3", "Execute change management strategy according to the methodology"),
    ("P", "PM-1.10.4", "Determine a change response to move the project forward"),
    ("P", "PM-1.11.1", "Define resource requirements and needs"),
    ("P", "PM-1.11.2", "Communicate resource requirements"),
    ("P", "PM-1.11.3", "Manage suppliers/contracts"),
    ("P", "PM-1.11.4", "Plan and manage procurement strategy"),
    ("P", "PM-1.11.5", "Develop a delivery solution"),
    ("P", "PM-1.12.1", "Determine the requirements (what, when, where, who, etc.) for managing the project artifacts"),
    ("P", "PM-1.12.2", "Validate that the project information is kept up to date (i.e., version control) and accessible to all stakeholders"),
    ("P", "PM-1.12.3", "Continually assess the effectiveness of the management of the project artifacts"),
    ("P", "PM-1.13.1", "Assess project needs, complexity, and magnitude"),
    ("P", "PM-1.13.2", "Recommend project execution strategy (e.g., contracting, finance)"),
    ("P", "PM-1.13.3", "Recommend a project methodology/approach (i.e., predictive, agile, hybrid)"),
    ("P", "PM-1.13.4", "Use iterative, incremental practices throughout the project life cycle (e.g., lessons learned, stakeholder engagement, risk)"),
    ("P", "PM-1.14.1", "Determine appropriate governance for a project (e.g., replicate organizational governance)"),
    ("P", "PM-1.14.2", "Define escalation paths and thresholds"),
    ("P", "PM-1.15.1", "Recognize when a risk becomes an issue"),
    ("P", "PM-1.15.2", "Attack the issue with the optimal action to achieve project success"),
    ("P", "PM-1.15.3", "Collaborate with relevant stakeholders on the approach to resolve the issues"),
    ("P", "PM-1.16.1", "Discuss project responsibilities within team"),
    ("P", "PM-1.16.2", "Outline expectations for working environment"),
    ("P", "PM-1.16.3", "Confirm approach for knowledge transfers"),
    ("P", "PM-1.17.1", "Determine criteria to successfully close the project or phase"),
    ("P", "PM-1.17.2", "Validate readiness for transition (e.g., to operations team or next phase)"),
    ("P", "PM-1.17.3", "Conclude activities to close out project or phase (e.g., final lessons learned, retrospective, procurement, financials, resources)"),
    # --- Domain 2: People & Leadership ---
    ("L", "PM-2.01.1", "Interpret the source and stage of the conflict"),
    ("L", "PM-2.01.2", "Analyze the context for the conflict"),
    ("L", "PM-2.01.3", "Evaluate/recommend/reconcile the appropriate conflict resolution solution"),
    ("L", "PM-2.02.1", "Set a clear vision and mission"),
    ("L", "PM-2.02.2", "Support diversity and inclusion (e.g., behavior types, thought process)"),
    ("L", "PM-2.02.3", "Value servant leadership (e.g., relate the tenets of servant leadership to the team)"),
    ("L", "PM-2.02.4", "Determine an appropriate leadership style (e.g., directive, collaborative)"),
    ("L", "PM-2.02.5", "Inspire, motivate, and influence team members/stakeholders (e.g., team contract, social contract, reward system)"),
    ("L", "PM-2.02.6", "Analyze team members and stakeholders' influence"),
    ("L", "PM-2.02.7", "Distinguish various options to lead various team members and stakeholders"),
    ("L", "PM-2.03.1", "Appraise team member performance against key performance indicators"),
    ("L", "PM-2.03.2", "Support and recognize team member growth and development"),
    ("L", "PM-2.03.3", "Determine appropriate feedback approach"),
    ("L", "PM-2.03.4", "Verify performance improvements"),
    ("L", "PM-2.04.1", "Organize around team strengths"),
    ("L", "PM-2.04.2", "Support team task accountability"),
    ("L", "PM-2.04.3", "Evaluate demonstration of task accountability"),
    ("L", "PM-2.04.4", "Determine and delegate level(s) of decision-making authority"),
    ("L", "PM-2.05.1", "Determine required competencies and elements of training"),
    ("L", "PM-2.05.2", "Determine training options based on training needs"),
    ("L", "PM-2.05.3", "Allocate resources for training"),
    ("L", "PM-2.05.4", "Measure training outcomes"),
    ("L", "PM-2.06.1", "Appraise stakeholder skills"),
    ("L", "PM-2.06.2", "Deduce project resource requirements"),
    ("L", "PM-2.06.3", "Continuously assess and refresh team skills to meet project needs"),
    ("L", "PM-2.07.1", "Determine critical impediments, obstacles, and blockers for the team"),
    ("L", "PM-2.07.2", "Prioritize critical impediments, obstacles, and blockers for the team"),
    ("L", "PM-2.07.3", "Use network to implement solutions to remove impediments, obstacles, and blockers for the team"),
    ("L", "PM-2.07.4", "Re-assess continually to ensure impediments, obstacles, and blockers for the team are being addressed"),
    ("L", "PM-2.08.1", "Analyze the bounds of the negotiations for agreement"),
    ("L", "PM-2.08.2", "Assess priorities and determine ultimate objective(s)"),
    ("L", "PM-2.08.3", "Verify objective(s) of the project agreement is met"),
    ("L", "PM-2.08.4", "Participate in agreement negotiations"),
    ("L", "PM-2.09.1", "Evaluate engagement needs for stakeholders"),
    ("L", "PM-2.09.2", "Optimize alignment between stakeholder needs, expectations, and project objectives"),
    ("L", "PM-2.09.3", "Build trust and influence stakeholders to accomplish project objectives"),
    ("L", "PM-2.10.1", "Break down situation to identify the root cause of a misunderstanding"),
    ("L", "PM-2.10.2", "Survey all necessary parties to reach consensus"),
    ("L", "PM-2.10.3", "Support outcome of parties' agreement"),
    ("L", "PM-2.10.4", "Investigate potential misunderstandings"),
    ("L", "PM-2.11.1", "Examine virtual team member needs (e.g., environment, geography, culture, global, etc.)"),
    ("L", "PM-2.11.2", "Investigate alternatives (e.g., communication tools, colocation) for virtual team member engagement"),
    ("L", "PM-2.11.3", "Implement options for virtual team member engagement"),
    ("L", "PM-2.11.4", "Continually evaluate effectiveness of virtual team member engagement"),
    ("L", "PM-2.12.1", "Communicate organizational principles with team and external stakeholders"),
    ("L", "PM-2.12.2", "Establish an environment that fosters adherence to the ground rules"),
    ("L", "PM-2.12.3", "Manage and rectify ground rule violations"),
    ("L", "PM-2.13.1", "Allocate the time to mentoring"),
    ("L", "PM-2.13.2", "Recognize and act on mentoring opportunities"),
    ("L", "PM-2.14.1", "Assess behavior through the use of personality indicators"),
    ("L", "PM-2.14.2", "Analyze personality indicators and adjust to the emotional needs of key project stakeholders"),
]

# ---------------------------------------------------------------------------
# Item assignments  (competency_code -> [item_ids])
#
# Item IDs are the actual SQLite course_items.id values confirmed against DB.
# Archived items (PM-819 Project/Process Flowchart) and unmatched items
# (Forum: Communications, Forum: Shell Case Fabricators, PM-817 Project Charter/
# Scope Statement, PM-813 Project Management Plan, LD-804 Interview with a Leader,
# PM-813 Rescuing a Troubled Project) are excluded.
# ---------------------------------------------------------------------------
ITEM_ASSIGNMENTS = {
    # 1.1 Execute project with urgency
    "PM-1.01.1": [696, 749, 780, 782, 781, 788, 855, 783],
    "PM-1.01.2": [749, 751, 855],
    "PM-1.01.3": [697, 716, 856],
    # 1.2 Manage communications
    "PM-1.02.1": [728, 790, 872, 383],
    "PM-1.02.2": [728, 726, 790, 872, 383],
    "PM-1.02.3": [742, 879],
    "PM-1.02.4": [756, 880],
    # 1.3 Assess and manage risks
    "PM-1.03.1": [690, 722, 794, 869],
    "PM-1.03.2": [690, 755, 794, 869],
    # 1.4 Engage stakeholders
    "PM-1.04.1": [687, 728, 872],
    "PM-1.04.2": [687, 728, 872],
    "PM-1.04.3": [687, 872],
    "PM-1.04.4": [686, 728, 872],
    # 1.5 Plan and manage budget and resources
    "PM-1.05.1": [697, 724, 868],
    "PM-1.05.2": [697, 721, 868],
    "PM-1.05.3": [701, 742, 868],
    "PM-1.05.4": [686, 719, 868],
    # 1.6 Plan and manage schedule
    "PM-1.06.1": [697, 714, 856],
    "PM-1.06.2": [697, 714, 856],
    "PM-1.06.3": [688, 714, 856],
    "PM-1.06.4": [697, 742, 856],
    "PM-1.06.5": [699, 742, 856],
    "PM-1.06.6": [686, 742, 856],
    # 1.7 Plan and manage quality
    "PM-1.07.1": [749, 802, 875],
    "PM-1.07.2": [749, 802, 875],
    "PM-1.07.3": [749, 802, 875],
    # 1.8 Plan and manage scope
    "PM-1.08.1": [687, 712, 854],
    "PM-1.08.2": [687, 713, 716, 854],
    "PM-1.08.3": [687, 716, 856],
    "PM-1.08.4": [701, 745, 870],
    # 1.9 Integrate project planning
    "PM-1.09.1": [689, 856],
    "PM-1.09.2": [689],
    "PM-1.09.3": [689, 742],
    "PM-1.09.4": [689, 742],
    "PM-1.09.5": [689],
    # 1.10 Manage project changes
    "PM-1.10.1": [689, 711, 789, 870],
    "PM-1.10.2": [689, 711, 789, 870],
    "PM-1.10.3": [689, 745, 870],
    "PM-1.10.4": [689, 745, 870],
    # 1.11 Plan and manage procurement
    "PM-1.11.1": [699, 719, 770, 871],
    "PM-1.11.2": [699, 719, 770, 871],
    "PM-1.11.3": [691, 769, 871],
    "PM-1.11.4": [770, 871],
    "PM-1.11.5": [770, 871],
    # 1.12 Manage project artifacts
    "PM-1.12.1": [691, 802],
    "PM-1.12.2": [691, 745, 802],
    "PM-1.12.3": [691, 745, 802],
    # 1.13 Determine appropriate methodology
    "PM-1.13.1": [691, 729, 781, 793, 856],
    "PM-1.13.2": [691, 729, 770, 781, 856],
    "PM-1.13.3": [691, 729, 781, 856],
    "PM-1.13.4": [691, 728, 722, 745, 744, 756, 795, 856],
    # 1.14 Establish project governance
    "PM-1.14.1": [691, 711, 787, 854],
    "PM-1.14.2": [691, 711, 787, 854],
    # 1.15 Manage project issues
    "PM-1.15.1": [686, 755, 794, 880],
    "PM-1.15.2": [686, 755, 794, 880],
    "PM-1.15.3": [686, 755, 794, 880],
    # 1.16 Ensure knowledge transfer
    "PM-1.16.1": [691, 719, 874],
    "PM-1.16.2": [719, 874],
    "PM-1.16.3": [719, 874],
    # 1.17 Plan and manage closure/transitions
    "PM-1.17.1": [706],
    "PM-1.17.2": [706, 744],
    "PM-1.17.3": [706, 744],
    # 2.1 Manage conflict
    "PM-2.01.1": [775, 376],
    "PM-2.01.2": [775, 376],
    "PM-2.01.3": [775, 376],
    # 2.2 Lead a team
    "PM-2.02.1": [705, 788, 854, 379],
    "PM-2.02.2": [379],
    "PM-2.02.3": [379],
    "PM-2.02.4": [379],
    "PM-2.02.5": [705, 379],
    "PM-2.02.6": [872],
    "PM-2.02.7": [379],
    # 2.3 Support team performance
    "PM-2.03.1": [383],
    "PM-2.03.2": [383],
    "PM-2.03.3": [383],
    "PM-2.03.4": [383],
    # 2.4 Empower team members
    "PM-2.04.1": [872, 383],
    "PM-2.04.2": [383],
    "PM-2.04.3": [383],
    "PM-2.04.4": [383],
    # 2.5 Ensure team is trained
    "PM-2.05.1": [719, 874, 383],
    "PM-2.05.2": [874, 383],
    "PM-2.05.3": [719, 868, 383],
    "PM-2.05.4": [383],
    # 2.6 Build a team
    "PM-2.06.1": [383],
    "PM-2.06.2": [705, 719, 868, 383],
    "PM-2.06.3": [383],
    # 2.7 Address impediments
    "PM-2.07.1": [705, 757],
    "PM-2.07.2": [],
    "PM-2.07.3": [383],
    "PM-2.07.4": [383],
    # 2.8 Negotiate project agreements
    "PM-2.08.1": [775],
    "PM-2.08.2": [775],
    "PM-2.08.3": [775],
    "PM-2.08.4": [775],
    # 2.9 Collaborate with stakeholders
    "PM-2.09.1": [728, 790, 872, 376, 379],
    "PM-2.09.2": [728, 790, 872, 376, 379],
    "PM-2.09.3": [728, 872, 376, 379],
    # 2.10 Build shared understanding
    "PM-2.10.1": [691, 777, 376, 379],
    "PM-2.10.2": [691, 777, 376, 379],
    "PM-2.10.3": [691, 777, 376, 379],
    "PM-2.10.4": [691, 777, 376, 379],
    # 2.11 Engage virtual teams
    "PM-2.11.1": [719, 383],
    "PM-2.11.2": [383],
    "PM-2.11.3": [383],
    "PM-2.11.4": [383],
    # 2.12 Define team ground rules
    "PM-2.12.1": [872, 383],
    "PM-2.12.2": [854],
    "PM-2.12.3": [854],
    # 2.13 Mentor stakeholders
    "PM-2.13.1": [686, 856, 383],
    "PM-2.13.2": [686, 383],
    # 2.14 Emotional intelligence
    "PM-2.14.1": [376],
    "PM-2.14.2": [376],
}

# ---------------------------------------------------------------------------
# Items with no DB match — noted for traceability, not inserted
# ---------------------------------------------------------------------------
UNMATCHED_ITEMS = [
    "PM-800: Forum: Communications (ext id 388) — not found in canvas_courses",
    "PM-800: Forum: Shell Case Fabricators (ext id 393) — not found in canvas_courses",
    "PM-813: Project Management Plan (ext id 408) — not found; may be embedded in another item",
    "PM-813: Rescuing a Troubled Project Case Study (ext id 454) — not found in canvas_courses",
    "PM-817: Project Charter/Scope Statement (ext id 449) — not found in canvas_courses",
    "LD-804: Interview with a Leader (ext id 452) — not found in canvas_courses",
    "PM-819: Project/Process Flowchart (ext id 434) — ARCHIVED, intentionally excluded",
]


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- Remove existing PM competency data ---
    c.execute("SELECT id FROM competency_categories WHERE letter IN ('P','L')")
    existing_cat_ids = [r[0] for r in c.fetchall()]
    if existing_cat_ids:
        placeholders = ",".join("?" * len(existing_cat_ids))
        c.execute(f"SELECT id FROM competencies WHERE category_id IN ({placeholders})", existing_cat_ids)
        existing_comp_ids = [r[0] for r in c.fetchall()]
        if existing_comp_ids:
            placeholders2 = ",".join("?" * len(existing_comp_ids))
            c.execute(f"DELETE FROM item_competency_links WHERE competency_id IN ({placeholders2})", existing_comp_ids)
            c.execute(f"DELETE FROM competencies WHERE id IN ({placeholders2})", existing_comp_ids)
        c.execute(f"DELETE FROM competency_categories WHERE id IN ({placeholders})", existing_cat_ids)
        print(f"Cleared existing PM categories: {existing_cat_ids}")

    # --- Insert categories ---
    cat_id_map = {}
    for letter, title in CATEGORIES:
        c.execute("INSERT INTO competency_categories (letter, title) VALUES (?, ?)", (letter, title))
        cat_id_map[letter] = c.lastrowid
    print(f"Inserted {len(CATEGORIES)} categories: {list(cat_id_map.keys())}")

    # --- Insert competencies ---
    comp_id_map = {}
    for letter, code, name in COMPETENCIES:
        cat_id = cat_id_map[letter]
        c.execute(
            "INSERT INTO competencies (category_id, code, name, description) VALUES (?, ?, ?, ?)",
            (cat_id, code, name, ""),
        )
        comp_id_map[code] = c.lastrowid
    print(f"Inserted {len(COMPETENCIES)} competencies")

    # --- Insert item links ---
    link_count = 0
    seen = set()
    for code, item_ids in ITEM_ASSIGNMENTS.items():
        comp_id = comp_id_map[code]
        for item_id in item_ids:
            key = (item_id, comp_id)
            if key in seen:
                continue
            seen.add(key)
            c.execute(
                "INSERT INTO item_competency_links (item_id, competency_id) VALUES (?, ?)",
                (item_id, comp_id),
            )
            link_count += 1
    print(f"Inserted {link_count} item-competency links")

    conn.commit()
    conn.close()

    # --- Summary ---
    print()
    print("=== Unmatched items (not linked) ===")
    for note in UNMATCHED_ITEMS:
        print(f"  - {note}")


if __name__ == "__main__":
    main()
