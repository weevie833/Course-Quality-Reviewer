# Canvas Course Scraper — Quick Start (Streamlit)

## 60 Seconds to Running

### Step 1: Install Streamlit
```bash
pip install streamlit
```

### Step 2: Navigate to Plugin Folder
```bash
cd /path/to/canvas-course-scraper
```

### Step 3: Launch the App
```bash
streamlit run streamlit_app.py
```

✅ Browser opens automatically at `http://localhost:8501`

---

## Using the App

1. **Enter working directory** (where your imscc_exports/ folder is)
2. **Click "Load Directory"**
3. **Review courses** displayed
4. **Click "Extract All Courses"**
5. **Wait for completion**
6. **View results** in output folder

---

## Folder Layout Required

```
your-working-directory/
├── imscc_exports/
│   ├── HRM 805/         ← Canvas export folders
│   ├── LD 804/
│   └── ...
└── canvas_courses/      ← Auto-created with outputs
```

---

## To Stop the App

Press **Ctrl+C** in terminal

---

## That's It!

No configuration, no servers, no complexity.

For more details, see: `STREAMLIT_SETUP.md`
