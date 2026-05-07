#!/usr/bin/env python3
"""Canvas Course Scraper — Clean Professional UNH Interface"""

import streamlit as st
import sys
import hashlib
from pathlib import Path
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import shutil

# Configure page - hide sidebar toggle
st.set_page_config(
    page_title="Canvas Course Scraper — UNH",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar toggle button and set white background
st.markdown("""
<style>
    /* Hide sidebar toggle */
    button[kind="header"] { display: none; }
    [data-testid="stSidebarCollapseButton"] { display: none; }

    /* White background */
    .stApp { background-color: white !important; }
    .main { background-color: white !important; }

    /* Remove extra padding */
    .block-container { padding-top: 0 !important; padding-bottom: 2rem !important; }

    /* Clean divider */
    hr { border-top: 3px solid #001B43 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# Add skills directory to path
skills_dir = Path(__file__).parent / "skills" / "canvas-course-scraper-launcher"
sys.path.insert(0, str(skills_dir))

from validators import DirectoryValidator, NameValidator
from parsers import ModuleMetadataParser, RubricsParser
from extractors import CourseContentExtractor
from output_writer import OutputWriter
from reporters import ExtractionReporter

def calculate_manifest_hash(manifest_path):
    """Calculate MD5 hash of manifest file for change detection."""
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

# ============= HEADER =============
st.markdown("""
<div style='background-color: #001B43; margin: 0 calc(-50vw + 50%) 2rem calc(-50vw + 50%); padding: 1rem 1.5rem;'>
    <div style='display: flex; align-items: center; justify-content: space-between;'>
        <div style='display: flex; align-items: center; gap: 1rem;'>
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <div>
                    <div style='color: white; font-size: 0.75rem; font-weight: 600;'>University of</div>
                    <div style='color: white; font-size: 0.75rem; font-weight: 600;'>New Hampshire</div>
                </div>
                <div style='color: white; font-size: 1.5rem; opacity: 0.5;'>|</div>
                <div style='color: white; font-size: 0.95rem; font-weight: 500;'>Canvas Course Extractor</div>
            </div>
        </div>
        <div style='color: white; opacity: 0.7;'>Program Mapping System</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============= WORKFLOW GUIDE =============
st.markdown("""
<div style='background-color: #f0f4f9; border-left: 4px solid #001B43; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;'>
    <strong style='color: #001B43;'>How It Works:</strong> This tool extracts course content from Canvas IMSCC exports.
    <br>Select courses below, click EXTRACT, and the system will pull all pages, assignments, discussions, quizzes, and rubrics into clean HTML files.
</div>
""", unsafe_allow_html=True)

# Configuration - use parent directory of this script's location
SCRIPT_DIR = Path(__file__).parent.parent  # Goes up from canvas-course-scraper to Program-Mapping-System
WORKING_DIR = str(SCRIPT_DIR.absolute())

# Session state
if 'courses' not in st.session_state:
    st.session_state.courses = []
if 'reextract_courses' not in st.session_state:
    st.session_state.reextract_courses = {}
if 'extraction_just_completed' not in st.session_state:
    st.session_state.extraction_just_completed = False

# Setup paths
root_path = Path(WORKING_DIR)
imscc_dir = root_path / "imscc_exports"
output_dir = root_path / "canvas_courses"

# ============= COURSE DISCOVERY =============
st.markdown("<h2 style='color: #001B43; margin-bottom: 0.5rem; margin-top: 1.5rem;'>Step 1: Select Courses</h2>", unsafe_allow_html=True)
st.markdown("<div style='background-color: #001B43; height: 3px; margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 1.5rem;'>Below are all available courses. <strong>NEW</strong> courses are ready to extract. Previously extracted courses can be re-extracted if needed.</p>", unsafe_allow_html=True)

name_validator = NameValidator()
all_courses = []
new_updated_courses = []
previously_extracted_courses = []

if not imscc_dir.exists():
    st.error(f"❌ imscc_exports/ folder not found at {imscc_dir}")
else:
    subfolders = [d for d in imscc_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not subfolders:
        st.info("ℹ️ No course folders found in imscc_exports/")
    else:
        for folder in sorted(subfolders):
            folder_name = folder.name
            manifest_path = folder / "imsmanifest.xml"

            is_valid, course_id, issue = name_validator.validate(folder_name)

            if not is_valid or not manifest_path.exists():
                continue

            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Extract course title - try both namespace prefixes
                ns = {'lom': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest'}
                title_elem = root.find('.//lom:title/lom:string', ns)

                # If not found with 'lom' prefix, try 'lomimscc' prefix
                if title_elem is None:
                    ns = {'lomimscc': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest'}
                    title_elem = root.find('.//lomimscc:title/lomimscc:string', ns)

                course_title = title_elem.text if title_elem is not None and title_elem.text else "Unknown"

                course = {
                    'folder_path': folder,
                    'folder_name': folder_name,
                    'course_id': course_id,
                    'course_title': course_title,
                    'manifest_path': manifest_path,
                }

                # Determine if NEW or previously extracted
                output_folder = output_dir / course_id
                log_file = output_folder / f"{course_id}_extraction-log.json"

                is_new = False
                extracted_date = None

                if not output_folder.exists():
                    is_new = True
                elif not log_file.exists():
                    is_new = True
                else:
                    try:
                        current_hash = calculate_manifest_hash(manifest_path)
                        with open(log_file) as f:
                            log_data = json.load(f)
                            stored_hash = log_data.get('manifest_hash', '')
                            extracted_at = log_data.get('extracted_at', '')

                            if current_hash and stored_hash and current_hash == stored_hash:
                                try:
                                    dt = datetime.fromisoformat(extracted_at)
                                    extracted_date = dt.strftime("%m/%d/%y %I:%M %p")
                                except:
                                    extracted_date = "date unavailable"
                            else:
                                is_new = True
                    except:
                        is_new = True

                course['is_new'] = is_new
                course['extracted_date'] = extracted_date
                all_courses.append(course)

                if is_new:
                    new_updated_courses.append(course)
                else:
                    previously_extracted_courses.append(course)

            except Exception as e:
                continue

    if all_courses:
        # Initialize checkbox state
        for course in all_courses:
            if course['course_id'] not in st.session_state.reextract_courses:
                st.session_state.reextract_courses[course['course_id']] = False

        # Display NEW courses (no course ID column - just full title)
        if new_updated_courses:
            for course in new_updated_courses:
                col1, col2 = st.columns([5, 1], gap="small")
                with col1:
                    st.markdown(f"<span style='font-size: 1rem; color: #333;'>{course['course_title']}</span>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<span style='background-color: #CBDB2A; color: #001B43; padding: 0.3rem 0.8rem; border-radius: 3px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;'>NEW</span>", unsafe_allow_html=True)

        # Blue divider
        st.markdown("<div style='background-color: #001B43; height: 3px; margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

        # Previously extracted courses collapsible
        if previously_extracted_courses:
            with st.expander("Previously Extracted Courses", expanded=False):
                # Column headers
                col1, col2, col3 = st.columns([3, 1.5, 1], gap="small")
                with col1:
                    st.markdown("<strong style='color: #001B43;'>Course Name</strong>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<strong style='color: #001B43;'>Previously Extracted</strong>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<strong style='color: #001B43;'>Re-Extract</strong>", unsafe_allow_html=True)

                st.divider()

                # Course rows
                for course in previously_extracted_courses:
                    col1, col2, col3 = st.columns([3, 1.5, 1], gap="small")
                    with col1:
                        st.markdown(f"<span style='color: #333;'>{course['course_title']}</span>", unsafe_allow_html=True)
                    with col2:
                        st.caption(course['extracted_date'] or "Never")
                    with col3:
                        st.session_state.reextract_courses[course['course_id']] = st.checkbox(
                            "Re-extract",
                            value=st.session_state.reextract_courses.get(course['course_id'], False),
                            key=f"reextract_{course['course_id']}",
                            label_visibility="collapsed"
                        )

        st.session_state.courses = all_courses
    else:
        st.warning("⚠️ No valid courses found. Check folder naming (should be: XXX 999)")

# Initialize conflict resolution state
if 'conflict_resolutions' not in st.session_state:
    st.session_state.conflict_resolutions = {}

# ============= EXTRACTION =============
if st.session_state.courses:
    st.markdown("<h2 style='color: #001B43; margin-bottom: 0.5rem; margin-top: 2rem;'>Step 2: Extract Courses</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color: #001B43; height: 3px; margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 1.5rem;'>Click the EXTRACT button to begin processing the courses you selected above.</p>", unsafe_allow_html=True)

    # ============= CONFLICT DETECTION =============
    # Detect which courses have existing folders
    courses_to_extract = []
    for course in st.session_state.courses:
        output_folder = output_dir / course['course_id']
        if not output_folder.exists():
            courses_to_extract.append(course)
        elif st.session_state.reextract_courses.get(course['course_id'], False):
            courses_to_extract.append(course)

    # Find conflicts (courses with existing folders that will be re-extracted)
    conflicts = []
    for course in courses_to_extract:
        output_folder = output_dir / course['course_id']
        if output_folder.exists():
            conflicts.append(course)

    # Show conflict resolution UI if there are conflicts
    if conflicts:
        st.markdown("<div style='background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 6px; padding: 1.5rem; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #856404; margin-top: 0;'>⚠️ Course Folder Conflicts Detected</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #856404; margin-bottom: 1rem;'>The following courses already have extracted folders. Choose whether to <strong>Replace</strong> or <strong>Skip</strong> each one.</p>", unsafe_allow_html=True)

        for course in conflicts:
            col1, col2, col3 = st.columns([3, 1, 1], gap="small")
            with col1:
                st.markdown(f"<span style='color: #333; font-weight: 500;'>{course['course_id']}: {course['course_title']}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("Replace", key=f"replace_{course['course_id']}", use_container_width=True):
                    st.session_state.conflict_resolutions[course['course_id']] = "replace"
                    st.rerun()
            with col3:
                if st.button("Skip", key=f"skip_{course['course_id']}", use_container_width=True):
                    st.session_state.conflict_resolutions[course['course_id']] = "skip"
                    st.rerun()

            # Show current choice
            choice = st.session_state.conflict_resolutions.get(course['course_id'])
            if choice:
                if choice == "replace":
                    st.markdown(f"<span style='color: #28a745; font-size: 0.9rem;'>✓ Will be replaced</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #dc3545; font-size: 0.9rem;'>✗ Will be skipped</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #999; font-size: 0.9rem;'>Choose an option above</span>", unsafe_allow_html=True)
            st.divider()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.extraction_just_completed:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Refresh Course Status", use_container_width=True):
                st.session_state.extraction_just_completed = False
                st.rerun()
    else:
        # Style the button with custom CSS
        st.markdown("""
        <style>
            .stButton button {
                background-color: #001B43 !important;
                color: white !important;
                font-weight: 600 !important;
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            extract_clicked = st.button(
                "EXTRACT",
                use_container_width=True,
                key="extract_btn"
            )

        if extract_clicked:
            # Check if all conflicts have been resolved
            unresolved_conflicts = [c for c in conflicts if c['course_id'] not in st.session_state.conflict_resolutions]
            if unresolved_conflicts:
                st.error("❌ Please resolve all course conflicts before extracting. Choose 'Replace' or 'Skip' for each conflicting course.")
            else:
                st.markdown(f"<h3 style='color: #001B43;'>Processing...</h3>", unsafe_allow_html=True)

                progress_bar = st.progress(0)
                status_text = st.empty()

                # Include NEW courses + courses selected for re-extraction (excluding skipped ones)
                courses_to_extract = []
                for course in st.session_state.courses:
                    output_folder = output_dir / course['course_id']

                    if not output_folder.exists():
                        courses_to_extract.append(course)
                    elif st.session_state.reextract_courses.get(course['course_id'], False):
                        # Check if this course should be skipped
                        if st.session_state.conflict_resolutions.get(course['course_id']) != "skip":
                            courses_to_extract.append(course)

                success_count = 0
                error_count = 0
                results_list = []
                skipped_count = 0

                for idx, course in enumerate(courses_to_extract):
                    status_text.text(f"Processing {course['course_id']}...")

                    try:
                        course_id = course['course_id']
                        folder_path = course['folder_path']
                        course_title = course['course_title']

                        output_folder = output_dir / course_id

                        # Delete old folder if user chose "replace"
                        if st.session_state.conflict_resolutions.get(course_id) == "replace":
                            if output_folder.exists():
                                shutil.rmtree(output_folder)
                                status_text.text(f"Replacing {course_id}... (removing old folder)")

                        output_folder.mkdir(parents=True, exist_ok=True)

                        metadata_file = folder_path / "course_settings" / "module_meta.xml"
                        metadata_parser = ModuleMetadataParser(metadata_file) if metadata_file.exists() else None

                        rubrics_file = folder_path / "course_settings" / "rubrics.xml"
                        rubrics_parser = RubricsParser(rubrics_file) if rubrics_file.exists() else None

                        extractor = CourseContentExtractor(
                            folder_path,
                            metadata_parser,
                            rubrics_parser,
                            course_id,
                            course_title,
                            manifest_path=course['manifest_path']
                        )

                        extracted_data = extractor.extract_all()

                        writer = OutputWriter(output_folder)
                        file_count = writer.write_files(extracted_data)

                        # Calculate manifest hash for change detection
                        manifest_hash = calculate_manifest_hash(course['manifest_path'])

                        log_data = {
                            'course_id': course_id,
                            'course_title': course_title,
                            'extracted_at': datetime.now().isoformat(),
                            'file_count': file_count,
                            'manifest_hash': manifest_hash
                        }

                        log_file = output_folder / f"{course_id}_extraction-log.json"
                        with open(log_file, 'w') as f:
                            json.dump(log_data, f, indent=2)

                        reporter = ExtractionReporter(course_id, extracted_data)
                        report_text = reporter.generate_report()
                        report_file = output_folder / f"{course_id}_extraction-report.txt"
                        with open(report_file, 'w') as f:
                            f.write(report_text)

                        success_count += 1
                        results_list.append(f"✓ {course_id} ({file_count} files)")

                    except Exception as e:
                        error_count += 1
                        results_list.append(f"✗ {course['course_id']} - {str(e)}")

                    progress_bar.progress((idx + 1) / len(courses_to_extract))

            # Count skipped courses
            skipped_count = sum(1 for c in st.session_state.courses
                              if st.session_state.reextract_courses.get(c['course_id'], False)
                              and (output_dir / c['course_id']).exists()
                              and st.session_state.conflict_resolutions.get(c['course_id']) == "skip")

            # Results
            st.markdown(f"<h3 style='color: #001B43; margin-top: 2rem;'>✓ Extraction Complete</h3>", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Successful", success_count)
            with col2:
                st.metric("Errors", error_count)
            with col3:
                st.metric("Skipped", skipped_count)
            with col4:
                st.metric("Total", success_count + error_count + skipped_count)

            if error_count == 0:
                st.success("All extractions completed successfully! 🎉")
            else:
                st.warning("⚠️ Extraction completed with some errors. See details below.")

            # Results detail - only show if there are errors
            if error_count > 0:
                with st.expander("📋 Extraction Details", expanded=True):
                    for result in results_list:
                        if result.startswith("✓"):
                            st.markdown(f"<span style='color: #008647;'>{result}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='color: #D32F2F;'>{result}</span>", unsafe_allow_html=True)

            # Enhanced post-extraction feedback
            st.markdown("""
            <div style='background-color: #CBDB2A; border: 2px solid #001B43; border-radius: 6px; padding: 1.5rem; margin: 1.5rem 0;'>
                <h4 style='color: #001B43; margin-top: 0;'>✓ Next Steps</h4>
                <p style='color: #001B43; margin: 0;'><strong>All courses have been extracted.</strong> Refresh the application to check for new course additions.</p>
            </div>
            """, unsafe_allow_html=True)

            st.session_state.extraction_just_completed = True

# ============= FOOTER =============
st.markdown("")
st.markdown(f"""
<div style='text-align: center; color: white; font-size: 0.85rem; padding: 1.5rem; background-color: #001B43; margin: 0 calc(-50vw + 50%) -2rem calc(-50vw + 50%);'>
    <strong>Canvas Course Scraper v0.2.0</strong><br>
    University of New Hampshire | Program Mapping System
</div>
""", unsafe_allow_html=True)
