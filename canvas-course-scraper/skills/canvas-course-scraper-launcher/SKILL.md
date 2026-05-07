---
description: "Launch the Canvas Course Scraper batch processor. Extracts course content from IMSCC exports (pages, assignments, discussions, quizzes, rubrics) and generates clean HTML files with metadata headers for PLO/CLO mapping analysis."
triggers: ["extract canvas courses", "run canvas scraper", "process imscc exports", "launch course scraper"]
---

# Canvas Course Scraper — Launcher

##Overview

This skill launches the Canvas Course Scraper batch processor to extract course content from Canvas IMSCC exports.

## Quick Start

1. Provide your root working directory path (or let it prompt you)
2. The scraper validates your course folders
3. Review the confirmation list
4. Approve extraction
5. Watch real-time progress
6. Review extraction report

## Folder Structure

```
[your-root-directory]/
├── imscc_exports/           ← Your course exports go here
│   ├── HRM 805/
│   ├── LD 804/
│   └── ...
└── canvas_courses/          ← Output created automatically
    ├── HRM-805/
    ├── LD-804/
    └── ...
```

## Folder Naming Convention

Course folders must be named: `XXX 999` (3 letters, space, 3 numbers)
- Example: `HRM 805`, `LD 804`, `MGMT 710`
- Exception: `APST 695A` (with suffix letter) will prompt for confirmation

## Output Files

Each extraction creates:
- HTML files (pages, assignments, discussions, quizzes, rubrics) with metadata headers
- Extraction log (JSON) for staleness detection
- Extraction report (txt) showing extracted vs. ignored content

## For More Information

See the README in this plugin for detailed technical documentation.
