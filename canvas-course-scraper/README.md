# Canvas Course Scraper Plugin

**Version 0.2.0**

A Python-based batch processor for extracting course content from Canvas IMSCC exports, generating clean HTML files with metadata headers for PLO/CLO mapping analysis.

## Overview

This plugin automates the extraction of course content from Canvas IMSCC (IMS Common Cartridge) exports. It intelligently processes course structure, filters content according to specifications, resolves rubric references, and generates standardized output files ready for learning outcomes mapping work.

## Features

- **Batch Processing**: Process multiple courses in a single run
- **Smart Status Detection**: Automatically identifies NEW, UPDATED, and UNCHANGED courses
- **Content Type Support**: 
  - Pages (filtered by exclusion rules)
  - Assignments (with rubric references)
  - Discussions (with rubric references, excluding unassessed discussions)
  - Rubrics (complete rubric criteria and scoring)
- **Manifest-Based Processing**: Uses IMSCC manifest to build accurate file mappings
- **Metadata Headers**: Every extracted file includes structured metadata (content type, course, module, rubric reference)
- **Namespace-Aware Parsing**: Handles XML namespaces correctly across different IMSCC formats

## Installation

1. Save the plugin to your Cowork plugins directory
2. Restart Cowork to activate
3. Use the "Canvas Course Scraper" skill from your toolbar

## Quick Start

1. **Prepare your course exports**:
   ```
   /path/to/working/directory/
   ├── imscc_exports/
   │   ├── HRM 805/
   │   ├── LD 804/
   │   └── ...
   ```

2. **Run the scraper**:
   - Use the skill launcher or run directly:
   ```bash
   python3 scraper_main.py "/path/to/working/directory"
   ```

3. **Review outputs**:
   ```
   /path/to/working/directory/
   └── canvas_courses/
       ├── HRM-805/
       │   ├── HRM-805_assignment_*.html
       │   ├── HRM-805_discussion_*.html
       │   ├── HRM-805_page_*.html
       │   ├── HRM-805_rubric_*.html
       │   ├── HRM-805_extraction-report.txt
       │   └── HRM-805_extraction-log.json
   ```

## Extraction Criteria

### Pages
**Extracted**: All published pages EXCEPT:
- "Ongoing Instructor Notes for Future Reference"
- "About the Use of AI in This Course"
- "About Your Instructor"
- "Course Resources"
- "Home CPSO"
- Pages with "Faculty Quick Guides" in title
- Pages with "Getting Started Canvas Resources" in title
- Pages with "Rubric" in title

### Assignments
**Extracted**: All published assignments with assigned rubrics

### Discussions
**Extracted**: All published discussions with attached rubrics EXCEPT:
- "General Q & A"
- Discussions with "Introduction" in title (e.g., "Introductions")

*Note: A discussion is considered "assessed" (extracted) only if it has a rubric_identifierref in its topicMeta settings file.*

### Rubrics
**Extracted**: All course rubrics including:
- Rubric title
- Assessment criteria
- Competency levels and scoring

### Always Ignored
- Course syllabus
- Unpublished content
- Administrative pages
- Student resources pages

## Output Format

Each extracted file includes a metadata header:

```html
<!-- CONTENT-TYPE: [Page|Assignment|Discussion|Rubric] -->
<!-- COURSE: HRM-805 -->
<!-- MODULE: [Full Module Name] -->
<!-- TITLE: [Item Title] -->
<!-- RUBRIC-REF: [Rubric Name] -->
[HTML Content...]
```

### File Naming Convention

- **Pages**: `[COURSE-ID]_page_[sanitized-title].html`
- **Assignments**: `[COURSE-ID]_assignment_[sanitized-title].html`
- **Discussions**: `[COURSE-ID]_discussion_[sanitized-title].html`
- **Rubrics**: `[COURSE-ID]_rubric_[sanitized-title].html`

*Sanitization: Lowercase, special characters removed, hyphens for spaces, max 60 chars*

## Course Folder Naming

Course folders in `imscc_exports/` must follow the pattern:
- **Standard**: `XXX 999` (3 letters, space, 3 digits)
  - Example: `HRM 805`, `LD 804`, `MGMT 710`
- **With Suffix**: `XXXX 9995` (allows letter suffix)
  - Example: `APST 695A`

The scraper automatically converts folder names to standardized course IDs (e.g., `HRM 805` → `HRM-805`).

## Course Status Detection

The scraper automatically determines processing status:

- **NEW**: Course output folder doesn't exist yet
- **UPDATED**: Course folder exists but `imsmanifest.xml` has been modified since last extraction
- **UNCHANGED**: Course folder exists and manifest hasn't changed (skipped to save time)

## Technical Details

### Architecture

```
scraper_main.py           ← Entry point, orchestration
├── validators.py         ← Directory and folder name validation
├── parsers.py            ← XML parsing for metadata and rubrics
├── extractors.py         ← Content extraction with filtering
├── output_writer.py      ← HTML file generation with metadata
└── reporters.py          ← Extraction report generation
```

### Key Classes

- `CanvasCourseScraper`: Main orchestrator
- `DirectoryValidator`: Validates directory structure
- `NameValidator`: Validates course folder naming
- `ModuleMetadataParser`: Parses module structure and publication status
- `RubricsParser`: Extracts rubric definitions
- `CourseContentExtractor`: Main extraction logic
- `OutputWriter`: Generates output HTML files

### Discussion Extraction

Discussions are handled specially due to Canvas IMSCC structure:

1. **Two-File Pattern**:
   - Content file (imsdt_xmlv1p1): Contains title and HTML text
   - Settings file (topicMeta): Contains metadata including rubric_identifierref

2. **Manifest-Based Linking**:
   - `imsmanifest.xml` defines dependencies between content and settings files
   - Plugin parses these dependencies to build accurate file mappings

3. **Rubric Resolution**:
   - Reads `<rubric_identifierref>` from settings file
   - Resolves to human-readable rubric title from rubrics parser

## Examples

### Extracted Discussion with Rubric

```html
<!-- CONTENT-TYPE: Discussion -->
<!-- COURSE: HRM-805 -->
<!-- MODULE: Module 2: Evolving Role of HR -->
<!-- TITLE: Module 2 Discussion: HR transitioning from a transactional function to a strategic partner -->
<!-- RUBRIC-REF: BSTC Graduate Discussion Rubric -->

<p>While organizations face increasing complexity...</p>
```

### Ignored Discussion

The following are ignored and listed in the extraction report:
- "General Q & A" (exclusion rule)
- "Module 1 Discussion: Introductions" (contains "Introduction")
- Discussions without rubric references (unassessed)

## Troubleshooting

**Issue**: "No course folders found in imscc_exports/"
- **Solution**: Verify the `imscc_exports/` directory exists and contains course folders with correct naming (XXX 999 pattern)

**Issue**: "Extraction completed with errors"
- **Solution**: Check the extraction report for specific items that couldn't be processed; these may indicate XML format issues in the export

**Issue**: Fewer items extracted than expected
- **Solution**: Run the scraper and review the extraction report to see which items were ignored and why

## Development Notes

### Adding New Content Types

To add support for new content types (e.g., quizzes):

1. Add extraction method to `CourseContentExtractor` (e.g., `_extract_quizzes()`)
2. Call the method in `extract_all()`
3. Update the reporters to include the new type in the report
4. Test with course exports and verify metadata headers

### Extending Filters

To add new exclusion rules for pages or discussions:

1. Update `EXCLUDED_PAGE_TITLES` or `EXCLUDED_PAGE_CONTAINS` sets in `CourseContentExtractor`
2. Modify `_should_exclude_page()` or `_should_exclude_discussion()` methods
3. Test with course exports to verify filtering behavior

## Version History

**v0.2.0** (Current)
- Added discussion extraction with rubric references
- Implemented manifest-based discussion-to-settings file mapping
- Fixed XML namespace handling for imsdt content
- Improved extraction filtering for unassessed discussions

**v0.1.1**
- Initial release with pages, assignments, and rubric extraction
- Course status detection (NEW/UPDATED/UNCHANGED)
- Extraction reporting

## Support and Feedback

For issues, suggestions, or contributions, please provide:
- Course export that demonstrates the issue
- Steps to reproduce
- Expected vs. actual behavior
- Your Canvas LMS version

## License

This plugin is provided as-is for educational and institutional use.

---

**Created for**: Senior Instructional Designer, University
**Purpose**: Automating PLO/CLO mapping analysis workflow
**Status**: Active Development
