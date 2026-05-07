#!/usr/bin/env python3
"""Canvas Course Scraper — Main Orchestrator"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
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

class CanvasCourseScraper:
    """Main scraper orchestrator."""
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.imscc_dir = self.root_dir / "imscc_exports"
        self.output_dir = self.root_dir / "canvas_courses"
        self.courses = []

    def run(self):
        """Execute the full extraction pipeline."""
        print("\n" + "="*70)
        print("CANVAS COURSE SCRAPER — IMSCC BATCH PROCESSOR")
        print("="*70)
        print("\n[1/5] Validating directory structure...")
        validator = DirectoryValidator(self.root_dir, self.imscc_dir)
        if not validator.validate():
            print("✗ Validation failed. Please resolve the issues above.")
            return False
        print("✓ Directory structure is valid")
        print("\n[2/5] Discovering courses...")
        name_validator = NameValidator()
        courses = self._discover_courses(name_validator)
        if courses is None:
            print("✗ Discovery failed. Please resolve naming issues above.")
            return False
        self.courses = courses
        print(f"✓ Found {len(courses)} course(s)")
        print("\n[3/5] Checking course status...")
        self._determine_course_status()
        print("\n[4/5] Confirmation List")
        print("-" * 70)
        self._display_confirmation_list()
        print("\n" + "-" * 70)
        approval = input("\nProceed with extraction? (yes/no): ").strip().lower()
        if approval not in ['yes', 'y']:
            print("✗ Extraction cancelled.")
            return False
        print("\n[5/5] Extracting courses...\n")
        if not self._extract_all_courses():
            print("\n⚠ Extraction completed with errors (see above).")
        else:
            print("\n✓ All extractions completed successfully.")
        print("\n" + "="*70)
        print("✓ EXTRACTION PROCESS COMPLETE")
        print("="*70)
        print(f"\nOutput written to: {self.output_dir}\n")
        return True

    def _discover_courses(self, name_validator):
        """Scan imscc_exports/ and validate course folders."""
        courses = []
        halt_count = 0
        if not self.imscc_dir.exists():
            print(f"✗ imscc_exports/ directory not found at {self.imscc_dir}")
            return None
        subfolders = [d for d in self.imscc_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not subfolders:
            print(f"✗ No course folders found in imscc_exports/")
            return None
        for folder in sorted(subfolders):
            folder_name = folder.name
            manifest_path = folder / "imsmanifest.xml"
            is_valid, course_id, issue = name_validator.validate(folder_name)
            if not is_valid:
                print(f"  HALT  {folder_name:30} — {issue}")
                halt_count += 1
                continue
            if not manifest_path.exists():
                print(f"  HALT  {folder_name:30} — missing imsmanifest.xml")
                halt_count += 1
                continue
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
                course_title = self._extract_course_title(root)
                if not course_title:
                    print(f"  HALT  {folder_name:30} — could not extract course title")
                    halt_count += 1
                    continue
                courses.append({
                    'folder_path': folder,
                    'folder_name': folder_name,
                    'course_id': course_id,
                    'course_title': course_title,
                    'manifest_path': manifest_path,
                    'status': None,
                    'manifest_mtime': manifest_path.stat().st_mtime
                })
                print(f"  OK    {course_id:20} {course_title[:40]}")
            except Exception as e:
                print(f"  HALT  {folder_name:30} — error parsing manifest: {str(e)}")
                halt_count += 1
                continue
        if halt_count > 0:
            print(f"\n✗ {halt_count} folder(s) cannot be processed. Please resolve and try again.")
            return None
        return courses if courses else None

    def _extract_course_title(self, manifest_root):
        """Extract course title from imsmanifest.xml."""
        ns = {'lom': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest'}
        title_elem = manifest_root.find('.//lom:title/lom:string', ns)
        if title_elem is not None and title_elem.text:
            return title_elem.text
        return None

    def _determine_course_status(self):
        """Determine if each course is NEW, UPDATED, or UNCHANGED."""
        for course in self.courses:
            course_id = course['course_id']
            output_folder = self.output_dir / course_id
            log_file = output_folder / f"{course_id}_extraction-log.json"
            if not output_folder.exists():
                course['status'] = 'NEW'
            elif not log_file.exists():
                course['status'] = 'UPDATED'
            else:
                try:
                    with open(log_file) as f:
                        log_data = json.load(f)
                        log_time_str = log_data.get('extracted_at', '')
                        if log_time_str:
                            log_time = datetime.fromisoformat(log_time_str).timestamp()
                            manifest_time = course['manifest_mtime']
                            if manifest_time > log_time:
                                course['status'] = 'UPDATED'
                            else:
                                course['status'] = 'UNCHANGED'
                        else:
                            course['status'] = 'UPDATED'
                except:
                    course['status'] = 'UPDATED'

    def _display_confirmation_list(self):
        """Show the user a confirmation list of courses."""
        print("\nFound {} course(s):\n".format(len(self.courses)))
        for course in self.courses:
            status = course['status']
            course_id = course['course_id']
            title = course['course_title'][:45]
            if status == 'NEW':
                status_str = "OK   "
            elif status == 'UPDATED':
                status_str = "WARN "
            else:
                status_str = "SKIP "
            print(f"  {status_str} {course_id:15} {title}")
        skipped = [c for c in self.courses if c['status'] == 'UNCHANGED']
        if skipped:
            print(f"\nNote: {len(skipped)} course(s) unchanged — will be skipped.")

    def _extract_all_courses(self):
        """Extract all NEW and UPDATED courses."""
        courses_to_extract = [c for c in self.courses if c['status'] != 'UNCHANGED']
        success_count = 0
        error_count = 0
        for course in courses_to_extract:
            try:
                if self._extract_course(course):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"✗ Unexpected error extracting {course['course_id']}: {str(e)}")
                error_count += 1
        print(f"\n{'='*70}")
        print(f"Extraction Summary:")
        print(f"  Successful: {success_count}")
        print(f"  Errors: {error_count}")
        print(f"{'='*70}")
        return error_count == 0

    def _extract_course(self, course):
        """Extract a single course."""
        course_id = course['course_id']
        course_title = course['course_title']
        folder_path = course['folder_path']
        print(f"\n✓ Processing {course_id}...")
        try:
            output_folder = self.output_dir / course_id
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
            print(f"    ✓ Extracted {file_count} files")
            print(f"    ✓ Report: {course_id}_extraction-report.txt")
            return True
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Entry point."""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = input("Enter the full path to your root working directory: ").strip()
    if not root_dir:
        print("✗ No directory provided.")
        sys.exit(1)
    scraper = CanvasCourseScraper(root_dir)
    success = scraper.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
