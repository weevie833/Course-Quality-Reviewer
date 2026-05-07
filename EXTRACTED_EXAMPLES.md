# Canvas Course Scraper — Extracted Content Examples

This document shows real examples from the HRM 805 course extraction (v0.2.0).

## Example 1: Extracted Assignment with Rubric

**File**: `HRM-805_assignment_module-1-submission-critical-thinking-exercise.html`

```html
<!-- CONTENT-TYPE: Assignment -->
<!-- COURSE: HRM-805 -->
<!-- MODULE: Module 1: Overview of HR&OD and Relevance to Organizational Outcomes -->
<!-- TITLE: Module 1 Submission: Critical Thinking Exercise -->
<!-- RUBRIC-REF: BSTC Graduate Project Assignment Rubric -->

<h2>Module 1 Critical Thinking Exercise</h2>
<p><strong>Objective:</strong> To examine how the course's frameworks apply to real organizational scenarios.</p>
<p><strong>Instructions:</strong></p>
<ol>
<li>Select an organization you work for (or one you're familiar with)</li>
<li>Analyze how workforce planning influences organizational strategy</li>
<li>Document your findings in a 2-3 page response</li>
</ol>
<p><strong>Grading:</strong> This assignment is graded using the BSTC Graduate Project Assignment Rubric.</p>
```

## Example 2: Extracted Discussion with Rubric

**File**: `HRM-805_discussion_module-2-discussion-hr-transitioning-from-a-transactional-fu.html`

```html
<!-- CONTENT-TYPE: Discussion -->
<!-- COURSE: HRM-805 -->
<!-- MODULE: Module 2: Evolving Role of HR and Impact of the Role of Leaders -->
<!-- TITLE: Module 2 Discussion: HR transitioning from a transactional function to a strategic partner -->
<!-- RUBRIC-REF: BSTC Graduate Discussion Rubric -->

<p>While organizations face increasing complexity, globalization, and digital disruption, the role of HR is shifting from a transactional function to a strategic partner. Leaders across all levels are expected to foster cultures of agility, resilience, and high performance.</p>
<p><strong>Reflecting on the evolving role of HR as a strategic partner, choose an organization (real or hypothetical) and respond to the following:</strong></p>
<ol style="list-style-type: decimal;">
<li><strong>HR Metrics and Strategic Alignment:</strong> Identify and analyze two key HR practices (e.g., onboarding, L&D, succession planning) and associated metrics (e.g., retention rate, performance ratings, skills gap analysis). How do these metrics demonstrate HR's strategic impact on organizational performance?</li>
<li><strong>Leadership and Data-Driven Decision-Making:</strong> Consider the role of organizational leaders in workforce planning. What data analytics tools or techniques should leaders use to make informed human capital decisions?</li>
</ol>
<p><strong>Reply Requirements:</strong></p>
<ul>
<li>Post an initial response by [DATE]</li>
<li>Reply to at least 2 classmate posts by [DATE]</li>
<li>Engage with analysis and evidence, not just agreement</li>
</ul>
```

## Example 3: Extracted Page with Course Overview

**File**: `HRM-805_page_course-overview.html`

```html
<!-- CONTENT-TYPE: Page -->
<!-- COURSE: HRM-805 -->
<!-- MODULE: Course Information -->
<!-- TITLE: Course Overview -->
<!-- RUBRIC-REF: NONE -->

<h1>HRM 805: Managing Human Resources in a Global Context</h1>
<p><strong>Course Credits:</strong> 3</p>
<p><strong>Delivery Method:</strong> Online</p>
<h2>Course Description</h2>
<p>This graduate-level course examines contemporary human resource management (HRM) and organizational development (OD) practices in multinational and globally-distributed organizations. Participants will explore how to develop and maintain competitive human capital in complex, dynamic, and geographically dispersed contexts.</p>
<h2>Learning Outcomes</h2>
<p>Upon completion of this course, learners will be able to:</p>
<ul>
<li>Analyze the strategic role of HR in global organizations</li>
<li>Design evidence-based talent management strategies</li>
<li>Assess organizational culture and change management approaches</li>
<li>Apply HR metrics to demonstrate business impact</li>
</ul>
```

## Example 4: Extracted Rubric with Criteria

**File**: `HRM-805_rubric_bstc-graduate-discussion-rubric.html`

```html
<!-- CONTENT-TYPE: Rubric -->
<!-- COURSE: HRM-805 -->
<!-- RUBRIC-ID: gfe3bce5bb071df26fbf98ac3a7ff2d28 -->
<!-- TITLE: BSTC Graduate Discussion Rubric -->
<!-- RUBRIC-REF: BSTC Graduate Discussion Rubric -->

<h2>BSTC Graduate Discussion Rubric</h2>
<p><strong>Used for:</strong> Course discussions, collaborative learning activities</p>
<table border="1" cellpadding="10">
<thead>
<tr>
<th>Criterion</th>
<th>Proficient (5 points)</th>
<th>Developing (3 points)</th>
<th>Beginning (1 point)</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Initial Post</strong></td>
<td>Post submitted on time with thoughtful analysis, clear evidence of reading assignment materials, and synthesis of course concepts.</td>
<td>Post submitted on time with some analysis and evidence of engagement with materials, but may lack depth.</td>
<td>Post submitted late or lacks evidence of engagement with materials and concepts.</td>
</tr>
<tr>
<td><strong>Peer Engagement</strong></td>
<td>Replies thoughtfully address peers' points, extend discussion with new evidence or perspectives, and model respectful dialogue.</td>
<td>Replies address peers' points but may lack depth or evidence. Generally respectful.</td>
<td>Minimal engagement with peers or responses that do not address their contributions.</td>
</tr>
<tr>
<td><strong>Academic Rigor</strong></td>
<td>Discussion integrates course concepts, external research, and practical examples with proper attribution.</td>
<td>Discussion references course materials with limited external sources or examples.</td>
<td>Discussion lacks reference to course materials or academic standards.</td>
</tr>
</tbody>
</table>
```

## Example 5: What Gets Ignored (Extraction Report)

**File**: `HRM-805_extraction-report.txt`

```
HRM-805 Extraction Report
======================================================================

Total items found: 45

EXTRACTED (23 files):
  - Assignment: Module 1 Submission: Critical Thinking Exercise
  - Assignment: Module 2 Submission: Critical Thinking Exercise
  [... 7 more assignments ...]
  - Discussion: Module 1 Discussion: HR's Strategic Value...
  - Discussion: Module 2 Discussion: HR transitioning...
  [... 6 more discussions ...]
  - Page: About The Strategic Hrod Final Paper
  - Page: Course Overview
  - Rubric: BSTC AI Reflection Rubric
  [... 3 more rubrics ...]

IGNORED (22 items):
  - General Q & A                              ← Excluded by title rule
  - Module 1 Discussion: Introductions         ← Excluded (contains "Introduction")
  - About The Use Of Ai In This Course         ← Excluded page
  - About Your Instructor                      ← Excluded page
  - Bstc Ai Reflection Rubric                  ← Duplicate in ignored list
  - Bstc Graduate Discussion Rubric            ← Duplicate in ignored list
  - Bstc Graduate Presentation Rubric          ← Duplicate in ignored list
  [... more ignored items ...]
```

## Metadata Header Format

Every extracted file begins with standardized metadata comments:

```html
<!-- CONTENT-TYPE: [Page|Assignment|Discussion|Rubric] -->
<!-- COURSE: [COURSE-ID] -->
<!-- MODULE: [Full Module Name] -->
<!-- TITLE: [Item Title] -->
<!-- RUBRIC-REF: [Rubric Name or NONE] -->
```

### Purpose of Metadata Headers

These headers enable:

1. **Programmatic Processing**: Tools can parse headers to organize content
2. **Relationship Mapping**: Links assignments/discussions to their rubrics
3. **Module Organization**: Maintains course structure information
4. **Quality Assurance**: Confirms extraction accuracy
5. **Downstream Integration**: Ready for PLO/CLO mapping tools

## File Organization Structure

After extraction, the course_courses folder contains:

```
canvas_courses/HRM-805/
├── HRM-805_assignment_module-1-submission-critical-thinking-exercise.html
├── HRM-805_assignment_module-2-submission-critical-thinking-exercise.html
├── HRM-805_assignment_module-3-submission-case-study-1-workforce-planning.html
├── HRM-805_assignment_module-4-submission-using-ai-to-enhance-recruitment.html
├── HRM-805_assignment_module-5-submission-case-study-2-learning-and-dev.html
├── HRM-805_assignment_module-6-submission-case-study-3-employee-engagement.html
├── HRM-805_assignment_module-6-submission-hrod-final-paper-outline.html
├── HRM-805_assignment_module-7-submission-completed-draft-of-final-strategic.html
├── HRM-805_assignment_module-8-submission-final-strategic-hrod-paper.html
│
├── HRM-805_discussion_module-1-discussion-hrs-strategic-value-based-on.html
├── HRM-805_discussion_module-2-discussion-hr-transitioning-from-a-transactional.html
├── HRM-805_discussion_module-3-discussion-strategic-workforce-planning-and.html
├── HRM-805_discussion_module-4-discussion-ethical-talent-acquisition-for.html
├── HRM-805_discussion_module-5-discussion-learning-and-development-ld-initiatives.html
├── HRM-805_discussion_module-6-discussion-compensation.html
├── HRM-805_discussion_module-7-discussion-cultural-differences.html
├── HRM-805_discussion_module-8-discussion-assessing-culture-in-global-workforce.html
│
├── HRM-805_page_about-the-strategic-hrod-final-paper.html
├── HRM-805_page_course-overview.html
│
├── HRM-805_rubric_bstc-ai-reflection-rubric.html
├── HRM-805_rubric_bstc-graduate-discussion-rubric.html
├── HRM-805_rubric_bstc-graduate-project-assignment-rubric.html
├── HRM-805_rubric_bstc-graduate-writing-assignment-rubric.html
│
├── HRM-805_extraction-report.txt    ← Detailed extraction summary
└── HRM-805_extraction-log.json      ← Timestamp for change detection
```

## Statistics

From HRM 805 real-world test:

- **Total Items Found**: 45 (pages, assignments, discussions, rubrics)
- **Successfully Extracted**: 23 (51.1%)
- **Filtered/Ignored**: 22 (48.9%)

**Breakdown**:
- Assignments: 9 extracted
- Discussions: 8 extracted (NEW in v0.2.0)
- Pages: 2 extracted
- Rubrics: 4 extracted
- Ignored discussions: 2 (General Q&A, Introductions)
- Ignored pages: 12 (excluded by rules)
- Ignored rubrics: 3 (duplicates)
- Ignored other: 5

## Integration with PLO/CLO Mapping

The extracted files are ready for import into mapping tools:

```
Mapping Workflow:
1. Extract courses → HTML files with metadata
2. Parse metadata headers → Identify relationships
3. Map assignments/discussions → Learning outcomes
4. Link rubrics → Competency levels
5. Generate alignment reports
```

Each file's metadata enables this downstream workflow automatically.

---

**Example Date**: April 20, 2026
**Plugin Version**: 0.2.0
**Test Course**: HRM 805: Managing Human Resources in a Global Context
