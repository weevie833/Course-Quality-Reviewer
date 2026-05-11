# Program Intelligence Interface — Project Reference

## What This App Is
A local RAG (retrieval-augmented generation) web application that serves as a plain-language
intelligence interface for graduate degree programs at UNH College of Professional Studies
(CPSO). Users — Deans, Program Directors, Instructional Designers, and Assessment Directors —
ask natural language questions about courses, assignments, PLOs, CLOs, rubrics, and professional
competencies. Claude answers definitively from actual course content stored in SQLite.

Interaction model: NotebookLM-style completeness. The system knows everything within the
defined program scope and answers from actual content, never from titles or hedged guesses.

The PII also serves as a **decision-support tool** for unmapped programs — when a program
director has not yet finalized competency-to-assignment mappings, the system uses semantic
alignment analysis to recommend where competencies would fit best. See Exploratory vs.
Definitive response framing in System Prompt Behavioral Rules.

## Programs in Scope (POC)
Four graduate programs, all Master's level. Courses overlap across programs.

| Short Name | Full Name |
|---|---|
| Leadership | MS in Leadership |
| Leadership-HRM | MS in Leadership — Human Resources Management Track |
| Leadership-ITM | MS in Leadership — Information Technology Management Track |
| Project Management | MS in Project Management |

Program selector in the UI allows filtering by one or more programs. No selection = all programs.

## File Structure

    Program-Mapping-System/
    ├── main.py                      # FastAPI backend — retrieval, context, routing, streaming
    ├── ingest.py                    # Canvas HTML → SQLite (full rebuild via main(); per-course via ingest_one_course())
    ├── ingest_competencies.py       # Populates LD A/B competency tables + item links (run after ingest.py)
    ├── ingest_pm_competencies.py    # Populates PM P/L competency tables + item links
    ├── ingest_shrm_competencies.py  # Populates SHRM BASK 2026 competency tables (no item links yet)
    ├── ingest_programs.py           # Populates program + program_courses tables (run after ingest.py)
    ├── sync.py                      # Auto-sync: fingerprint-based change detection, called at startup
    ├── generate_alignment.py        # One-time: Claude API → alignment_map.json + plo_clo_links
    ├── update_pm_competency_descriptions.py  # Loads PM competency descriptions + 5-level descriptors from CSV
    ├── canvas_courses/              # Extracted Canvas HTML files (one folder per course, 42 courses)
    ├── data/
    │   ├── program.db               # SQLite database (do NOT delete — competency + program data lives here)
    │   ├── alignment_map.json       # PLO→CLO and CLO→Item alignment (editable JSON)
    │   └── plos_clos.txt            # Source of truth for PLO and CLO text
    ├── static/
    │   └── index.html               # Single-page UI (vanilla JS, no build step)
    ├── .env                         # ANTHROPIC_API_KEY (not committed)
    └── CLAUDE.md                    # This file

## Running Locally

    cd "/Users/stevecovello/Documents/Claude/Projects/Program-Mapping-System"
    python3 -m uvicorn main:app --port 8000
    # open http://localhost:8000

**Do NOT use --reload** — sync.py runs on startup and re-ingest with --reload causes repeated runs.

## Database Schema

### Core tables
- `programs` — id, name, degree_type, short_name
- `courses` — course_id, title, required, **is_capstone** (INTEGER DEFAULT 0)
  - Capstone courses: LD-850, PM-850, CMPL-850. Assessed against PLOs, not CLOs.
- `course_items` — id, course_id, content_type, module, title, body_text, rubric_ref
  - content_type values: `Assignment`, `Discussion`, `Page`
  - Pages are never directly assessed but may contain full assignment descriptions
- `rubrics` — id, course_id, rubric_name, points_possible
- `rubric_criteria` — id, rubric_id, description, points, ratings_json
  - **description** now includes program prefix for all competency criteria (e.g., `LD-1.2.4-Self Awareness: Demonstrates Ethical Behavior`, `PM-2.10.1-Leadership-Understanding: Identify Misunderstanding`)
  - **ratings_json**: for standard rubric criteria, level text is in `long_description`; for competency criteria, level text is in `description` (e.g., `"Exemplary: full text..."`). Fetch functions fall back to `description` when `long_description` is empty.
- `item_rubric_links` — item_id, rubric_id
- `plos` — id, number, text, **program_id** (INTEGER REFERENCES programs(id))
  - PLOs are program-specific. Each program has its own set.
- `clos` — id, course_id, number, text
- `plo_clo_links` — plo_id, clo_id, strength, rationale
  - 828 links as of April 2026 (generated via generate_alignment.py)

### Program tables
- `program_courses` — id, program_id, course_id, role (required|elective), or_group
  - `or_group`: NULL = unconditional; same integer = choose one from group (e.g., HRM-810|HRM-830)
  - **5 courses have different roles across programs** — always use `get_course_role_lookup()` for
    program-aware required/elective labels, never the global `courses.required` flag:
    - LD-810: required in Leadership, Leadership-ITM; elective in Project Management
    - LD-821: required in Leadership; elective in Project Management
    - MGMT-805: required in Leadership-HRM; elective in Leadership
    - PM-800: required in Leadership-ITM, Project Management; elective in Leadership
    - PM-811: required in Project Management; elective in Leadership

### Competency tables
- `competency_categories` — id, letter, title
- `competencies` — id, category_id, code, name, description
  - `description` contains full proficiency indicator text for competency-to-assignment matching
- `competency_level_descriptors` — id, competency_id, level (1–5), descriptor
  - Used by LD A/B framework and PMI P/L framework; all 113 PM and 19 LD competencies complete
- `item_competency_links` — id, item_id, competency_id

### Alumni table
- `alumni` — alumni_id (PK), first_name, last_name, preferred_name, graduation_year, degree_type, program, honors, employment_status, job_title, employer, industry, engagement_level, volunteer_involvement, event_attendance_2024, city, state
  - 100 synthetic records loaded from SyntheticAlumni.rtf (testing only — people do not exist)
  - Contact, financial, and demographic fields intentionally excluded from the schema
  - Ingestion: `python3 ingest_alumni.py`

### Knowledge table
- `knowledge_articles` — id, domain, title, body_text, source_file
  - domain `ai_in_education`: 69 articles from AI in Education specialized knowledge collection
  - Retrieved via `search_knowledge_articles()` when `AI_KNOWLEDGE_QUERY_RE` fires in `build_context()`
  - Source: `/Users/stevecovello/Desktop/Claude Projects/_Program Intelligence Interface/Specialized knowledge/AI in Education/`
  - Re-ingest: `python3 ingest_ai_knowledge.py` (drops and recreates domain records)

### Sync table
- `course_ingest_log` — course_id (PK), fingerprint, ingested_at

### Current counts (42 courses ingested, as of April 2026)
- 4 programs, 57 program-course mappings
- 42 courses total, 3 flagged is_capstone (LD-850, PM-850, CMPL-850)
- 194 CLOs, 29 PLOs (program-specific: Leadership=6, Leadership-HRM=6, Leadership-ITM=8, Project Management=9)
- plo_clo_links: 828 (generated April 2026)
- Competency categories and counts:
  - LD/ITM Competencies — A (Individual Leadership): 8; B (Interpersonal & Organizational): 11
  - PMI Competencies — P (Project Management Processes): 62; L (People & Leadership): 51
  - SHRM Competencies — SHRM-1 through SHRM-6: 46 total (no item links yet)
  - Total: 10 internal categories, 178 competencies
- item_competency_links: 356 total
  - A/B links: 64 (LD-804, LD-820, LD-821*, LD-823, LD-810*, LD-850, COMM-800*)
    (* = placeholder — course not yet in DB; will resolve on re-run after course ingestion)
  - P/L links: 292 (PM courses) — with full 5-level descriptors (Novice→Exemplary)
  - SHRM links: 0 — pending program director decisions (by design, not a gap)

## Sync System (sync.py)
Called automatically via `main.py` lifespan on every server startup using `asyncio.to_thread()`.

- Computes a stat-based fingerprint `(filename, mtime, size)` for each `.html` file per course folder — no file reads
- Compares against `course_ingest_log`; re-ingests only changed/new courses
- **Auto-discovery:** Any folder in `canvas_courses/` with `.html` files is processed — no hardcoded allowlist
- Course title pulled from `{course_id}_extraction-log.json` (written by Cowork extractor)
- **Competency link preservation:** Before wipe, saves title→competency_id pairs; restores by title match after re-ingest
- All 42 courses currently up to date at startup

**Workflow for new courses:**
1. Export from Canvas → Cowork extractor → drops folder in `canvas_courses/`
2. Restart server → sync auto-detects new fingerprint → ingests → registers in `courses` table

## Tech Stack
- **Backend:** FastAPI + Python, streaming responses (StreamingResponse, text/plain)
- **Database:** SQLite with `sqlite3.Row` factory
- **AI:** Claude API — `claude-sonnet-4-6`, `max_tokens=8192`
- **Frontend:** Single HTML file, vanilla JS, no build step, markdown renderer built in

## Three-Tier RAG Architecture (main.py: build_context)

**Tier 1 — Always on (system prompt)**
PLOs (program-scoped when filter active), CLOs scoped to active program's courses (at startup
when no filter; per-request when program is selected), course title list, and active program
filter block (when programs selected).

**Tier 2 — Catalog inventory (program-wide queries)**
All item titles + metadata for ALL content types (Assignment, Discussion, Page), no body text.
Used when no specific course is mentioned and query is not inferential.
Scoped to program filter when active. Safe for ~40 courses; at 200+ needs a pre-filter step.

**Tier 3 — Body text**
Full body text for course-specific queries (always, no truncation).
Keyword-matched body snippets for program-wide detail queries (capped at 15 items).
Both scoped to program filter when active. Keyword search covers ALL content types.

**Inferential / Semantic Matching**
Triggered when user provides a text fragment and asks which assignments could assess it.
Replaces Tier 2/3 for these queries. Fetches body text for ALL items (Assignment, Discussion,
Page) in scope, truncated to 500 chars per item at word boundary. Claude performs semantic
comparison — keyword search is not used.

**Competency alignment path (broad queries)**
When a competency query fires without specific course mentions:
- Tier 2/3 skipped — competency catalog + assignment links are the relevant context
- `fetch_plo_clo_summary()` provides a compact PLO→CLO bridge (~2,700 tokens for PM)
  instead of `fetch_plo_alignment_chain()` which could exceed 99K tokens
- Back-reference check: if no codes in current message, scans last 4 assistant messages
  for competency codes (capped at 10) and loads their full detail blocks

**Back-reference anchoring**
When follow-up uses "this", "that assignment", "it":
- Scans last 4 assistant messages for bold markdown item titles
- Fetches those items by title match (full body text)
- Injects as "Pinned Items" at top of context

**History-aware course detection**
If no course ID in current message, scans last 4 assistant messages for course IDs.

## Key Functions in main.py

| Function | Purpose |
|---|---|
| `build_plos_block(program_short_names)` | Tier 1: PLOs scoped to active program(s); flat list for one program, grouped for multiple |
| `build_clos_block(course_ids)` | Tier 1: CLO text grouped by course; accepts optional course_ids list for scoping |
| `load_course_titles()` | Course ID → title + required flag (global; use get_course_role_lookup for program-aware labels) |
| `load_programs()` | All programs with course lists for app_state and /programs endpoint |
| `get_program_course_ids(names)` | Union of course IDs for selected program short_names |
| `get_course_role_lookup(program_names)` | Program-aware course_id → 'required'\|'elective'; required beats elective in multi-program |
| `fetch_items_for_course(course_id)` | All items (all content types) with full body text for one course |
| `load_program_inventory(course_ids)` | Tier 2: titles+metadata for all content types, no body text, optional scope |
| `search_item_bodies(query, course_ids)` | Tier 3: keyword search across all content types, scored, optional scope |
| `fetch_rubrics_for_course(course_id)` | All rubrics + full criteria for a course |
| `fetch_rubric_by_name(course_id, name)` | Single named rubric with full criteria |
| `fetch_plo_alignment_chain(plo_nums, focus_courses, role_lookup)` | Full PLO→CLO traversal with optional item drill-down; use only for specific PLO queries |
| `fetch_plo_clo_summary(program_short_names)` | Compact PLO→CLO bridge for broad competency queries (~2,700 tokens vs 99K for full chain) |
| `fetch_inferential_items(course_ids, body_limit, role_lookup)` | Semantic matching: all items with truncated body text |
| `extract_mentioned_items_from_history(h)` | Back-ref anchor: bold title → item lookup |
| `build_context(message, history, program_course_ids, program_names)` | Orchestrates all retrieval |
| `build_program_scope_block(program_names)` | System prompt block for active filter; includes competency framework assumption |
| `build_system_prompt(context, program_names)` | Assembles final system prompt |
| `get_competency_display_label(program_names)` | User-facing label for competency set(s) |
| `get_competency_categories_for_programs(program_names)` | Category letters for active program(s) |
| `fetch_competency_catalog(category_letters, label)` | All competencies (code + name) grouped by category |
| `fetch_competency_detail(code)` | Full description + level descriptors for one competency |
| `fetch_competency_assignment_links(...)` | Competency → assignment mapping, scoped |

## API Endpoints
- `GET /` — serves index.html
- `GET /programs` — returns program list with course memberships (used by UI pill selector)
- `POST /chat` — streaming chat; body: `{message, history, programs: [short_name, ...]}`
- `POST /download` — returns response text as file download
- `GET /health` — `{status, model}`

## Program Selector UI
- Pill bar above the input field, loaded from `/programs` on page load
- No pills active = all programs (unfiltered)
- Click pills to toggle; multiple selections = union of courses
- Active state: Seacoast Blue fill; inactive: parchment bg with border
- Tooltip on hover shows full program name
- Selected programs sent as `programs: [...]` array in every chat request
- **Scope confirmation modal** (`#scope-modal`) fires before sending when:
  - 0 programs selected: warns that results span all programs (may be very large)
  - 2+ programs selected: warns that same course may have different required/elective
    status across programs; names the selected programs in the message

## Retrieval Routing Logic (build_context)

1. Compute `role_lookup` (program-aware required/elective map) at top of function
2. Always: detect mentioned course IDs, PLO numbers, back-references
3. If back-reference: pin items from recent history → inject as "Pinned Items"
4. Compute `wants_competency` and `wants_comp_early` (includes back-reference scan of last 4 assistant messages)
5. If broad competency query (no specific courses): load `fetch_plo_clo_summary()` + skip Tier 2/3
6. If PLO numbers mentioned: fetch full alignment chain (PLO→CLO→Item)
7. If course IDs mentioned: full body text for those courses (all content types)
8. Else if inferential query detected: `fetch_inferential_items()` with program scope
9. Else: Tier 2 catalog inventory + Tier 3 keyword search
10. Always (if competency signals detected): fetch competency catalog and/or assignment links;
    if no codes in current message, scan recent assistant history for codes (cap 10)

### Inferential Query Detection
`INFERENTIAL_QUERY_RE` matches explicit phrasing:
- "suited to assess", "which assignments would", "assess this competency"
- "best assess", "could assess", "match this competency", "align with this competency", etc.

`QUOTED_FRAGMENT_RE` (20+ char quoted string) + competency-adjacent language also triggers
inferential mode.

## Domain Rules (encoded in system prompt and retrieval logic)
- **Pages are never assessed** — no rubric or competency assessment is linked to a Page
- **Pages may contain assignment descriptions** — when a prompt is too long for the assignment
  field, a separate Page holds the full description; Pages must be included in all retrieval
- **Assessable items only:** Assignments and Discussions receive rubric and competency assessments
- **Semantic matching cites the assignment, not the page** — even if a Page contains the
  description, the Assignment is the assessable artifact Claude should cite
- **All credits are 3 credits** — all graduate courses are 3 credits; use this for credit-hour calculations
- **External URLs:** System cannot access the internet. When a user provides a URL, respond with
  the configured message and offer to work with pasted text instead

## System Prompt Behavioral Rules
Defined in `SYSTEM_PROMPT_BASE` in main.py.

### Core retrieval and answer rules
1. Answer from content, never from titles (except broad catalog presence questions)
2. Answer definitively — no hedging
3. Lengthy responses: state scope, offer one-at-a-time or narrowing; deliver with counter (1 of N)
4. Let the user lead — no proactive gap surfacing; one direct follow-on only
5. CLO mapping: connect specific language in assignment to specific language in CLO
6. Rubrics: always show automatically; top level only; offer remaining levels after
7. Citations: PLOs/CLOs always by full text; courses with ID and title
8. No recanting prior assertions without contradictory evidence in current context
9. Back-references: assume most specific item from most recent response
10. Options: ANY user-facing choice (yes/no, co-orientation, follow-ons, multi-option) uses
    blockquote + bold format: `> **Option 1:** [descriptive phrase]`. Phrase must read naturally
    as a standalone user message. Never use bullet points for choices.
11. Known Gaps: course content (prompts, pages, rubrics) is fully loaded for ALL programs;
    SHRM competency links are pending director decision (not a missing integration)

### Exploratory vs. Definitive Response Framing (added April 2026)
All competency responses are framed based on whether formal links exist and what the user is asking:

- **Definitive**: formal links in retrieved context + user asking what IS assessed → direct factual statements, present tense, no hedging
- **Exploratory**: no formal links (e.g., Leadership-HRM), OR user uses exploratory phrasing
  ("might," "could," "recommend," "align well," "help me decide") → opens with a brief framing
  line naming the exploratory basis, ranks by semantic strength, closes with a note that results
  are a starting point for director review
- Leadership-HRM competency questions are always exploratory — no formal links have been
  established; the program director is actively using the PII to inform those decisions

### Program scope rule (added April 2026)
When analyzing CLO coverage or competency alignment for a program, ALL courses in that
program's curriculum must be included — not just courses whose prefix matches the program name.
Leadership-HRM includes required LD and MGMT courses; Leadership-ITM includes LD, PM, and CMPL
courses. The active program filter defines scope.

### Program button assumption (added April 2026)
When a program button is selected, the system assumes the user is asking about that program's
competency framework. No clarification question is asked about which framework applies.
Enforced in `build_program_scope_block()`.

### Co-orientation rules (added April 2026)
The system operates as a service provider to a professional client in a hierarchically superior
position. Clarification is always framed as the system seeking to serve better — never as
feedback on the quality of the user's query.
- High confidence queries: answer directly
- Medium confidence: answer most likely interpretation, name the alternative in one sentence
- Low confidence: ask one situated question naming two plausible interpretations
- Formula: "I can approach this as [X] or as [Y] — which is closer to what you need right now?"
- Prohibited: "Your question is unclear", "Could you be more specific?", "That's a broad question"

### Language — Program Quality (added April 2026)
Never use "weakness," "weaknesses," or "weak" to describe program elements. Substitutions:
- weakness/weaknesses → area for improvement / areas for improvement
- weak alignment → limited alignment / underdeveloped alignment
- weak coverage → limited coverage / underdeveloped coverage
Applies regardless of how the user phrases the question. Do not comment on the user's word choice.

### Language Analysis Preamble (added April 2026)
When a user explicitly requests an analysis of PLO, CLO, or competency language, open the
response with this preamble in italics (substitute [PLO/CLO/competency] with the specific type):

*This analysis evaluates the language of the [PLO/CLO/competency] against structural conventions
for well-formed learning outcomes. The findings reflect patterns in the language as written and
should be treated as a starting point, not a final assessment. Contextual factors — program
sequence, course-level scaffolding, or instructional intent — may address some of what the
analysis identifies as needing attention. Final language decisions are best made in coordination
with an instructional designer who can assist in crafting the best solution for your needs.*

Does NOT fire for factual retrieval questions.

### CLO Structural Quality — inline assessment (added April 2026)
**User-request-only** — evaluates CLO structural sufficiency (observable verb, subject content,
conditions, criteria) ONLY when the user explicitly asks for a quality or language assessment.
Does NOT fire automatically on alignment or coverage questions.
**Offer when listing:** When a response includes full CLO/PLO/competency text, append a single
brief offer to evaluate the language. Do not make this offer more than once per response.
Names what the CLO *needs* — never says it *lacks*.

### Online pedagogy context (added April 2026)
Seven always-on behavioral sections embedded in SYSTEM_PROMPT_BASE that silently shape all
advice about course and assignment design. These are never cited explicitly — they constrain
framing automatically:

1. **Online Learning Context** — broad async principles: structure is non-optional, active
   cognitive work over passive consumption, authentic contexts, structured discussions,
   deliberate teaching presence, metacognition in assignments, flexibility in when not what.

2. **Instructor Presence** — Community of Inquiry triad (Social / Teaching / Cognitive presence).
   All three in balance matter more than quantity. Every design question should be evaluated
   against whether it supports all three forms of presence.

3. **Student Readiness** — Students arrive with a sensemaking gap between F2F familiarity and
   online reality. Field-based failure patterns: negligible login regularity, skipping readings,
   inability to decode rubrics, throttled help-seeking. Course design must assume zero prior
   online learning literacy, especially in early modules.

4. **Discussion Prompt Design** — Five baseline assumptions (reduce ambiguity, coherence,
   uncertainty, explicitness, purpose) + six-part structure: Overture, Assignment, Questions,
   References to readings/media, Purpose, Tasks/Points. Applied when evaluating or advising
   on discussion prompts.

5. **Rich Media Pedagogical Wrapper** — Theoretical grounding: rich media alone does not cause
   learning; must be pedagogically situated (Covello, Dervin). Three-part wrapper: Before
   (relevance/credibility/provenance) → During (thematic focus, lean-in guidance) → After
   (discussion/reflection anchored to "How did the readings and media influence your position?").
   Connects to co-orientation design: both address the sensemaking gap when users lack guidance.

6. **AI Integration in Instruction** — Two-tier advisory (see below).

7. **CLO/PLO quality principles** — Four-element structure framework embedded for use in
   alignment quality assessment (see CLO Structural Quality above).

### AI Integration in Instruction — two-tier advisory (added April 2026)
Source: *Controlling AI in Instruction* (Covello) + AI-in-Education knowledge base (69 articles).

Tier 1 (always first — system prompt only, no retrieval):
- Co-orient to confirm what the user is trying to achieve
- Apply Three-Step Model (Determine what matters → Streamline → Transform)
- Name likely AIAS level; recommend ID collaboration
- Close with offer: "I can suggest specific activity ideas if you'd like"

**Alumni guest professional recommendations**
Triggered by `ALUMNI_QUERY_RE` (keywords: alumni, guest professional, guest speaker, industry professional, etc.). Loads full `fetch_alumni_catalog()` — all 100 records as a formatted table (engagement-ordered). Claude selects 3–5 matches based on industry/role alignment with the named course's CLOs and assignments, weighted by engagement level and volunteer involvement. Contact details are not stored. Outreach is always deferred to the Program Director or Advancement Office.

Tier 2 (only when user explicitly requests examples/activities):
- Retrieves from `knowledge_articles` table (domain: `ai_in_education`)
- Triggered when BOTH `AI_INTEGRATION_QUERY_RE` AND `AI_EXAMPLES_QUERY_RE` match
- Max 5 articles, 700-char snippets; cite source article; frame as ID conversation starters
- **Mandatory closing note:** Every Tier 2 response (developed prompt, structured activity recommendation) closes with a fixed italic paragraph directing the user to review with their ID partner before posting in Canvas. Mentions the AI Fundamentals e-book and the Canvas AI reflection rubric as institutional resources an ID can help locate and integrate.

Institutional goal embedded in system prompt: cultivate student agency over AI as operator,
not passive consumer. Avoid "clientification." Consistent curriculum-wide experiences matter
more than individual assignment design.

AIAS levels 1–5 (No AI → Full AI) are encoded in the system prompt for policy designation.

## Competency Assessment Rule
Graduate students are assessed **only against the competencies of their own degree program**, regardless of which course they are in. A shared course (e.g., PM-800 taken by both LD and PM students) will have separate program-specific rubrics for each program. If no program-specific rubric exists for a course, no competency assessment occurs for that program in that course — this is intentional, not a gap. Examples:
- LD students in PM-800 and PM-811: no LD competency rubrics exist; no LD competency links for those courses.
- LD-804 has both an LD rubric (LD Org Plan) and a PM rubric (PM Org Plan / Team Assessment / True Colors); each applies only to students in the respective program.

This rule governs all competency-to-item link ingestion and all future framework integrations (HRM, ITM).

## Competency Frameworks

### Code Format (standardized April 2026)
All competency codes use a program-prefix format consistently across all tables and displayed output:
- LD competencies: `LD-X.X.X` (e.g., LD-1.2.4, LD-2.3.1)
- PM competencies: `PM-X.XX.X` (e.g., PM-1.02.1, PM-2.10.1) — two-digit subcategory
- HRM competencies: `HRM-X.XX.XX` (e.g., HRM-1.01.01)
- ITM competencies: `ITM-X.X.X` (not yet defined)

**Rubric criteria descriptions** also use this prefix format (356 criteria updated April 2026):
`LD-1.2.4-Self Awareness: Demonstrates Ethical Behavior`, `PM-2.10.1-Leadership-Understanding: Identify Misunderstanding`

### LD Competencies (ingest_competencies.py)
- User-facing name: "LD Competencies" (Leadership program), "ITM Competencies" (Leadership-ITM program)
- 2 internal categories: A = Individual Leadership, B = Interpersonal & Organizational
- 19 competencies; codes: LD-1.X.X (formerly A.XX) and LD-2.X.X (formerly B.XX)
- Canvas substitutes numeric prefixes for A/B: A→1, B→2, so LD-1.2.4 = formerly A.24
- 5 rating levels per competency with full descriptors (competency_level_descriptors table)
- Item links: LD-804, LD-810, LD-820, LD-821, LD-823, LD-850 active; COMM-800 pending (course not yet ingested)
- Applied to: Leadership, Leadership-HRM, Leadership-ITM programs (LD courses only)
- Safe to re-run: drops and recreates all competency data each time

### PMI Competencies (ingest_pm_competencies.py + update_pm_competency_descriptions.py)
- User-facing name: "PMI Competencies" (Project Management program)
- 2 internal categories: P = Project Management Processes, L = People & Leadership
- 113 competencies from PMI PM Competencies 3.0; 292 item links across PM courses
- Full 5-level descriptors (Novice→Exemplary) loaded from PM-Outcome Set.csv
- Direct item ID mapping (not title matching) — IDs confirmed by querying course_items
- Applied to: Project Management program
- 7 unmatched items documented in UNMATCHED_ITEMS (archived or not in canvas)

### SHRM Competencies (ingest_shrm_competencies.py)
- User-facing name: "SHRM Competencies" (Leadership-HRM program)
- 6 internal categories: SHRM-1 through SHRM-6 (Leadership, Interpersonal, Business, People, Organization, Workplace)
- 46 competencies total; description field contains full proficiency indicator text
- **No item links** — mapping to assignments not yet finalized; program director is actively
  using the PII to make these decisions. All Leadership-HRM competency queries are exploratory.
- No rating level descriptors yet — awaiting program director
- Applied to: Leadership-HRM program (all program courses, including required LD and MGMT courses)

### Competency retrieval in main.py
`build_context()` detects competency queries via `COMPETENCY_CODE_RE` (matches `LD-X.X.X`,
`PM-X.XX.X`, `HRM-X.XX.XX`, `ITM-X.X.X`) and `COMPETENCY_QUERY_RE` (keywords: "competency",
"SHRM", "BASK", "PMI"). Helpers: `fetch_competency_catalog()`, `fetch_competency_detail()`,
`fetch_competency_assignment_links()`. Scoped to active program's frameworks via
`PROGRAM_COMPETENCY_MAP`. CLO block scoped to active program's courses per request.
`COURSE_ID_RE` includes PM-xxx and CMPL-xxx.

`fetch_plo_clo_summary()` provides a compact PLO→CLO bridge for broad competency queries.
Back-reference: if no competency codes in current message, scans last 4 assistant messages
for codes (capped at 10) and loads their full `fetch_competency_detail()` blocks.

## Ingestion Scripts — Run Order
When rebuilding from scratch:
1. `python3 ingest.py` — full DB rebuild from canvas_courses/
0b. `python3 ingest_alumni.py` — alumni table (can run any time; independent of other scripts)
2. `python3 ingest_competencies.py` — LD A/B competency framework + item links
3. `python3 ingest_pm_competencies.py` — PM P/L competency framework + item links
4. `python3 update_pm_competency_descriptions.py` — PM competency descriptions + 5-level descriptors from CSV
5. `python3 ingest_shrm_competencies.py` — SHRM BASK 2026 competency framework
6. `python3 ingest_programs.py` — program structure + course stubs
7. `python3 generate_alignment.py` — PLO/CLO alignment (~30 API calls, supports --resume flag)
8. `python3 ingest_ai_knowledge.py` — AI-in-Education reference articles → knowledge_articles table

For incremental updates: just restart the server — sync.py handles everything automatically.

## PLO/CLO Alignment Status
- `plo_clo_links` table has 828 links (generated April 2026 via generate_alignment.py)
- PLOs are program-specific (plos.program_id FK to programs.id)
- generate_alignment.py uses program-scoped PLOs (plo_id, not plo_number) to avoid ambiguity
- Supports --resume flag for crash recovery; writes incrementally to alignment_map.json

## Canvas Course Pipeline
.imscc export from Canvas → POST /admin/ingest (ingest_imscc.py) → canvas_courses/ (HTML per course)
→ sync.py on startup → program.db

Each course folder contains:
- `{course_id}_extraction-log.json` — contains `course_title`, used by sync for auto-registration
- `{course_id}_extraction-report.txt` — human-readable summary
- `*.html` files — assignments, discussions, pages, rubrics with metadata comment headers

## Known Gaps — Content Not Yet Integrated

All course content (assignment prompts, discussion prompts, pages, rubric criteria, CLOs, PLOs)
is fully loaded for all 42 courses across all 4 programs. The gaps below are metadata only —
missing competency-framework mappings, not missing course content.

### Leadership-HRM — SHRM Competencies
- **SHRM competency-to-assignment links:** No formal mapping has been finalized. The program
  director is actively using the PII to inform these decisions. All competency alignment
  questions for this program are treated as exploratory recommendations, not definitive results.
- **SHRM rating level descriptors:** The 5-level behavioral indicator text for each SHRM
  competency has not been provided. Also awaiting the program director.
- SHRM competency catalog text (descriptions, codes, names) IS present — 46 competencies.
  All Leadership-HRM course content (HRM, LD, and MGMT courses) IS fully loaded.

### Leadership-ITM — ITM Competencies (CMPL courses)
- **Framework not yet determined:** Which competency framework applies to CMPL courses in
  the Leadership-ITM program is unknown. No competency-to-assignment links exist for CMPL
  courses in this context.
- LD courses in the ITM program do have LD Competency links (shared with the Leadership program).
- CMPL course content IS fully loaded.

## Frontend UI Behavior (index.html — updated April 2026)

- **Program selection required:** Send button is disabled until at least one program pill is
  active. Hovering shows CSS tooltip: "Select at least one program to begin."
- **Hint text** lives in the program selector row (left of pills), not below the input. Reads
  "Select at least one program to begin" when none active; "Enter to send · Shift+Enter for
  new line" when active.
- **3+ programs warning:** Selecting a third pill injects an in-chat assistant message recommending
  no more than two programs at a time. User can still proceed.
- **2-program modal:** Fires before send when exactly two programs are active (required/elective
  status warning). Does not fire for 3+ (in-chat warning already shown at selection time).
- **Option buttons:** After any response containing `> **Option N:** [phrase]` blocks, clickable
  buttons appear below the bubble labeled with the descriptive phrase. Clicking sends that phrase
  as the user's message. All buttons disabled after one is clicked.
- **Option hint:** "You can select an option above or type your own reply below." appears beneath
  option buttons; hidden when a button is clicked.
- **Welcome / newChat text:** "Ask questions about PLO coverage, CLO alignment, assignments, and
  rubrics across any program."

## Recent Implementation Changes (May 2026)

### History Trimming for Rate Limit Management
**Problem:** Long conversations hit Anthropic's tokens-per-minute rate limit because the full conversation history was sent with every request, causing exponential growth of prompt size.

**Solution:** In `main.py` `/chat` route, conversation history sent to the Claude API is now capped at the last 6 messages (3 turns of user/assistant exchange). The full history is still passed to `build_context()` for back-reference anchoring and other retrieval logic, so conversational continuity and context awareness are unaffected.

**Files changed:** `main.py` lines ~1665–1675 (chat route).

**Result:** Rate limit errors eliminated. Sessions can now run longer without hitting TPM limits. The fix is transparent to users.

### Visualization Feature: Mermaid Diagrams and Chart.js
**Feature:** Users can now explicitly request visual representations (diagrams, charts, mind maps, flowcharts) which are rendered interactively in the browser using Mermaid.js v11 and Chart.js v4.

**Trigger:** Query must contain explicit visualization language detected by `VISUALIZATION_QUERY_RE` (matches: "diagram", "chart", "mind map", "visualize", "flow chart", etc.). Claude is NOT prompted to produce visualizations proactively.

**How it works:**
1. Frontend detects `VISUALIZATION_QUERY_RE` match in user message
2. Injects `VISUALIZATION_INSTRUCTIONS` into system prompt (conditional injection — zero overhead for non-visualization queries)
3. Claude outputs fenced code blocks tagged ` ```mermaid ` or ` ```chartjs ` containing text-based definitions
4. During streaming, placeholder divs are rendered with loading text
5. After stream completes, `renderVisualizations()` calls Mermaid.render() or Chart() to transform the code blocks into interactive graphics
6. Error fallbacks display friendly error messages if syntax is invalid

**System Prompt Guidance:**
- `VISUALIZATION_INSTRUCTIONS` (lines ~107–145 in main.py) explicitly tells Claude it is outputting *text* in a specific format, not rendering graphics. This works around Claude's training conviction that it is text-only. The instruction includes worked examples.
- Removed the phrase "Use plain text only" from line 1561 (was overly broad and blocked visualization output).

**Frontend Changes:**
- `index.html`: Added Mermaid.js and Chart.js CDN script tags (lines ~485–486)
- Added `.viz-block`, `.viz-mermaid`, `.viz-chartjs` CSS classes (lines ~462–483)
- Updated `renderMarkdown()` to extract fenced visualization blocks BEFORE HTML escaping, then reinsert them as placeholder divs (lines ~622–660)
- Added `renderVisualizations()` async function (lines ~895–919) that initializes Mermaid and Chart.js
- Updated streaming handler to call `await renderVisualizations(bubble)` after stream completes (line ~836)
- Added Mermaid initialization: `mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' })` (line ~893)

**Example use cases that now work:**
- *"Show me a diagram of how PLO 1 maps to the CLOs"* → Mermaid flowchart
- *"Visualize the competency coverage as a bar chart"* → Chart.js bar chart
- *"Give me a mind map of the PM curriculum"* → Mermaid mindmap

**Plain text trees vs. fenced blocks:**
- If Claude chooses to output an ASCII/plain text tree diagram (not a Mermaid diagram), it should NOT use backticks. The instruction clarifies this distinction (lines ~142–145).

**Known limitations:**
- Mermaid diagrams are capped at 15 nodes for readability; Claude notes total count if subsetting
- Both Mermaid and Chart.js have error fallbacks that display friendly error messages
- The feature only works when explicitly requested (proactive visualizations disabled to conserve inference)

**Files changed:**
- `main.py` (lines ~100–145 for regex and instructions, line ~1614 for conditional injection)
- `index.html` (multiple sections; see above)

## Planned / Deferred Work
- **SHRM item links + level descriptors:** Awaiting program director (Leadership-HRM).
- **ITM competency framework for CMPL courses:** Awaiting decision on which framework applies.
- **COMM-800 competency links:** Course not yet ingested. Will resolve automatically once
  ingested and ingest_competencies.py is re-run. (LD-821 and LD-810 already resolved.)
- **PLO/CLO quality review feature:** Bring in PLO Evaluator knowledge base (principles.md +
  examples.csv). Inline advisory similar to CLO quality check, applied at program outcome level.
- **CLO Tier 1 block scoping:** When no program is selected, do not load CLOs in Tier 1 —
  they are too broad to be useful across all programs. Scope CLOs only when a program is active.
  Priority: implement before the next program is added.
- **Canvas API integration (Phase 1):** Replace manual IMSCC export pipeline with direct Canvas
  REST API ingestion. Requires Canvas API token from UNH Canvas admin. sync.py fingerprint
  detection → Canvas webhooks. This is the highest-value infrastructure improvement.
- **LTI 1.3 integration (Phase 2):** Embed PII in Canvas via LTI launch + OAuth token for API
  access. Requires LTI 1.3 Developer Key from Canvas admin and UNH IT security review.
- **200+ course scaling:** Tier 2 inventory and inferential retrieval will exceed context limits.
  Needs pre-filter step (lightweight Claude call to identify relevant courses first).
- **Testing and refinement of all April 2026 system prompt additions:** Co-orientation rules,
  CLO quality inline assessment, online pedagogy context blocks, AI integration two-tier
  advisory, and rich media wrapper advisory have not yet been tested in live use.

## Ethical / Compliance Notes
- FERPA: No student data used or stored
- IP: Source material is property of the University System of New Hampshire
- Accessibility: UI should meet ADA standards
