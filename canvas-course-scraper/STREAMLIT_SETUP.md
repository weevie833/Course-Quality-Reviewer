# Canvas Course Scraper — Streamlit Frontend Setup

## Quick Start (5 minutes)

### 1. Install Streamlit
```bash
pip install streamlit
```

### 2. Run the App
Navigate to the plugin directory and run:
```bash
streamlit run streamlit_app.py
```

This will automatically open your browser to `http://localhost:8501`

### 3. Use the App

1. **Enter working directory** in the sidebar (where your imscc_exports folder is)
2. **Load Directory** to scan for courses
3. **Review** the courses found
4. **Extract All Courses** to process them
5. **Check results** in the canvas_courses output folder

## Folder Structure

```
your-working-directory/
├── imscc_exports/
│   ├── HRM 805/
│   ├── LD 804/
│   └── ...
└── canvas_courses/          ← Created automatically with outputs
    ├── HRM-805/
    ├── LD-804/
    └── ...
```

## Course Folder Naming

Course folders must follow the pattern: `XXX 999`
- Example: `HRM 805`, `LD 804`, `MGMT 710`

## What Happens During Extraction

For each course, the app will:
1. ✓ Validate the IMSCC export structure
2. ✓ Parse course metadata and rubrics
3. ✓ Extract pages, assignments, discussions, rubrics
4. ✓ Apply filtering rules (exclude unpublished, etc.)
5. ✓ Generate HTML files with metadata headers
6. ✓ Create extraction report showing what was extracted

## Output Files

For each course extracted, you'll get:
```
canvas_courses/HRM-805/
├── HRM-805_assignment_*.html        ← Assignments with rubric refs
├── HRM-805_discussion_*.html         ← Discussions with rubric refs
├── HRM-805_page_*.html              ← Pages
├── HRM-805_rubric_*.html            ← Rubrics
├── HRM-805_extraction-report.txt    ← Summary of what was extracted
└── HRM-805_extraction-log.json      ← Timestamp for change tracking
```

## Status Indicators

- 🟢 **NEW**: Course not yet extracted
- 🟡 **UPDATED**: Course source file changed since last extraction
- ⚪ **SKIP**: Course unchanged (will be skipped)

## Troubleshooting

### "Directory not found"
- Verify the full path is correct
- Use absolute paths (e.g., `/Users/username/Documents/...`)

### "No valid courses found"
- Ensure folders are named like `HRM 805` (3 letters, space, 3 digits)
- Check that imscc_exports/ folder exists at that location

### Extraction seems slow
- Normal for large courses (200+ items)
- Progress updates in real-time

### Port 8501 already in use
```bash
streamlit run streamlit_app.py --server.port 8502
```

## For Your Colleagues

Share with colleagues:
1. This folder with all files
2. Tell them to: `pip install streamlit && streamlit run streamlit_app.py`
3. They enter their own working directory path
4. Done!

No setup, no servers, no installation needed beyond Streamlit.
