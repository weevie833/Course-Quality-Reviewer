# Course Quality Reviewer — Project Reference

## What This App Is
A standalone Canvas course quality evaluation tool. A course director uploads a `.imscc` export
file; the app extracts all course content and runs Claude API evaluations against 8 quality
standards (based on OSCQR), producing evidence bullets, verdicts (Met / Partially Met / Not Met),
and gap notes for each sub-standard. Results can be saved as a formatted Word document.

Users: Course directors, instructional designers, and deans at UNH College of Professional Studies.

## Repository
GitHub: https://github.com/weevie833/Course-Quality-Reviewer

## File Structure

    Course Quality Reviewer/
    ├── main.py                   # FastAPI backend — upload, evaluation, Word export
    ├── ingest_imscc.py           # .imscc extraction → HTML files per content type
    ├── quality_standards.py      # STANDARDS dict — 8 standards, sub-standard interpretations
    ├── extracted_courses/        # {course_id}/{timestamp}/ — versioned extraction output
    │   └── COM-680/
    │       └── 20260624_140804/  # meta.json + *.html files
    ├── templates/
    │   └── UNH_CQR_Template.docx # Word report template
    ├── static/
    │   └── index.html            # Single-page UI (vanilla JS, no build step)
    ├── .env                      # ANTHROPIC_API_KEY (not committed)
    └── CLAUDE.md                 # This file

## Running Locally

    lsof -ti :8001 | xargs kill -9 && python3 -m uvicorn main:app --port 8001
    # open http://localhost:8001

**Do NOT use --reload.**

## Tech Stack
- **Backend:** FastAPI + Python, `asyncio.to_thread` for Claude API calls
- **AI:** Claude API — `claude-sonnet-4-6`, `max_tokens=8192`
- **Extraction:** python-docx (syllabus), zipfile + xml.etree (QTI quizzes), html.parser
- **Frontend:** Single HTML file, vanilla JS, no build step

## API Endpoints
- `GET /` — serves index.html
- `GET /health` — `{status, model}`
- `POST /upload` — accepts .imscc; extracts to `extracted_courses/{course_id}/{timestamp}/`
- `GET /course/current` — returns current loaded course from app_state
- `POST /evaluate/{standard_num}` — runs Claude evaluation for one standard (1–8)
- `POST /download/docx` — generates Word report from UNH_CQR_Template.docx
- `POST /chat` — chat with course content as context

## Course ID / Directory Naming
- `course_code` from Canvas `course_settings.xml` (e.g. "COM 680") → `COM-680` via `_clean_course_id`
- Regex: `([A-Za-z]+)\s+(\d{3,4})` — strips section numbers and term info
- Term info lives in `course_title` only; multiple term exports of same course → same subdirectory
- Version limit: 5 per course (configurable via `MAX_COURSE_VERSIONS`)
- `meta.json` in each version dir: `{course_id, course_title, timestamp, incomplete_standards, evaluation}`

## Extraction (ingest_imscc.py)
- Reads `imsmanifest.xml` + `course_settings/module_meta.xml` for structure
- Content types extracted: Assignment, DiscussionTopic, WikiPage, Quizzes::Quiz, Rubrics, Syllabus
- **Syllabus**: extracts from `.docx` via python-docx; walks `doc.element.body` children in order
  so tables (grading breakdown, schedule) appear inline — NOT just `doc.paragraphs`
- **Quizzes**: parses QTI XML; falls back to `non_cc_assessments/{ident}.xml.qti` for Canvas-native quizzes
- Output: `{course_id}_{type}_{slug}.html` with comment header metadata per file
- `EXCLUDED_PAGE_PATTERNS` = [] (no filtering)

## HTML Stripping (_strip_html in main.py)
Uses `html.parser.HTMLParser` (NOT regex — bare `<` in content would swallow thousands of chars):
- `<img>` → emits `[Image: alt='...']` or `[Image: no alt text]`
- `<iframe>` → emits `[Canvas-embedded video (likely Kaltura): "title" — captioning requires human verification]`
  or `[YouTube video: ...]` / `[Kaltura/hosted video: ...]` based on src
- `<script>`, `<style>` → skipped entirely

## Content Sort Order (_module_sort_key)
Items sorted: Syllabus (0) → Course Overview & Resources (1) → Module 1–N (2, N) → Other (3)

## Quality Standards (quality_standards.py)
`STANDARDS` dict, keys 1–8. Sub-standard counts: 1→9, 2→5, 3→6, 4→5, 5→4, 6→4, 7→4, 8→7

Key interpretation rules:
- **6.2**: All CQR courses are 100% async — absence of Zoom/Teams must NOT be flagged
- **7.2**: ADA reference anywhere in syllabus satisfies the standard
- **8.3**: Canvas template provides heading hierarchy — absence of H1/H2/H3 in extracted content must NOT be flagged
- **8.5**: Lists all `[video: ...]` placeholders from _strip_html; marks Partially Met; flags each
  video for human captioning verification in Canvas

## Evaluation Output (Claude JSON)
```json
{
  "substandards": [
    {
      "id": "1.3",
      "description": "Communication guidelines...",
      "evidence": "- In the About Discussions section...\n- In the Expectations...",
      "gaps": "- Insufficient: No formal netiquette document...",
      "verdict": "Partially Met"
    }
  ]
}
```
- `evidence`: one bullet per item, hierarchical location format ("In the [Module] module, in the '[Item]' page/assignment/discussion...")
- `gaps`: `"- Missing: ..."` or `"- Insufficient: ..."` bullets when Partially Met/Not Met; `""` when Met
- `verdict`: `"Met"` / `"Partially Met"` / `"Not Met"`
- JSON robustness: fence stripping + `json_repair` fallback in `_run_standard_evaluation()`

## Word Export (_build_docx in main.py)
- Template: `templates/UNH_CQR_Template.docx`
- First body paragraph uses "Header" paragraph **style** (not a page header) — contains `[Course ID and title]`
  placeholder replaced with full course title
- Body cleared from first bold sub-standard paragraph onwards; content rebuilt programmatically
- Structure: Standard heading (bold, 12pt) → blank → sub-standard description (bold Normal) →
  `Verdict: ` (bold) + verdict value (normal) → evidence bullets → Gaps section (amber label + amber bullets)

## Frontend (static/index.html)
Single-page app, vanilla JS. Key state:
```javascript
state = {
  course, evaluation, evaluationComplete, activeStandard,
  isStreaming, isEvaluating, pendingFile, chatHistory,
  uploadAbortController,   // AbortController for upload fetch
  evalAbortControllers,    // AbortController[] for evaluation fetches (one per standard)
}
```

### Upload flow
1. User clicks "Upload Course File" → file picker
2. If course already loaded: replace-modal fires
3. If at version limit (5): version-modal fires, offers to discard oldest
4. `uploadFile(file, discardOldest)`:
   - `showProcessing()` → button becomes "Processing…" (disabled) + Stop button appears + header progress bar animates
   - Fetch `/upload` with `AbortController` signal
   - On success: `onCourseLoaded()` → shows Begin Evaluation screen
   - On abort (`stopUpload()`): alert + restore upload prompt
   - On error: show error status + restore upload prompt

### Evaluation flow
1. `beginEvaluation()` → `runEvaluation([1..8])`
2. Panel shows "Evaluating all 8 standards…" + **Stop Evaluation** button (centered)
3. Header spinner + progress bar active
4. `Promise.allSettled` fires all 8 `/evaluate/N` calls in parallel, each with own AbortController
5. `stopEvaluation()` aborts all controllers → returns to Begin Evaluation screen
6. On complete: sidebar buttons enabled, SAVE DOCX enabled, panel shows completion message

### Key functions
- `showUploadPrompt()` — blank state with Upload Course File button
- `showProcessing()` — swaps button to Processing…, adds Stop button, activates header bar
- `stopUpload()` — aborts upload AbortController
- `stopEvaluation()` — aborts all eval AbortControllers
- `showBeginEvaluation()` — course loaded, ready to evaluate
- `runEvaluation(standards[])` — parallel eval with abort support
- `renderEvalContent(data)` — renders sub-standards with evidence + amber gaps section
- `renderBulletList(text, cssClass)` — splits `\n`-delimited bullets into `<ul>`
- `saveAsDocx()` — POSTs to `/download/docx`, triggers browser download
- `resetApp()` — full state clear: course + evaluation + chat; returns to upload prompt

### UI elements
- No header Upload button — only "Upload Course File" in main panel
- RESET button in header — full state clear
- SAVE DOCX button in footer — disabled until evaluation complete
- Gaps rendered with amber "GAPS" label (`color: #B45309`) + amber bullet text (`color: #92400E`)
- Sidebar Standard 1–8 buttons disabled until evaluation complete; active standard highlighted

## IP / Compliance Note
Course content (assignments, syllabus, rubrics, pages) is sent to the Anthropic API.
Anthropic does not train on API data. 30-day retention for safety monitoring.
For production deployment across CPSO, a vendor DPA with Anthropic is recommended.
No student data (FERPA not implicated).

## Known Issues / Deferred Work
- **Compare to prior version**: button present but shows placeholder only — not yet implemented
- **Standard 3 evidence count**: 10–14 bullets per sub-standard (may be too many)
- **7.2 verdict accuracy**: needs re-evaluation after the _strip_html regex fix surfaced ADA text
- **Standard 1.9**: peer response guidance NOT required for intro discussions (per interpretation)
