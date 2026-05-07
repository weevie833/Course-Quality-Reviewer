"""Output file writer — writes extracted content to HTML files with metadata headers."""
import re
from pathlib import Path
from typing import Dict

class OutputWriter:
    """Writes extracted files to disk with metadata headers."""
    def __init__(self, output_folder):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def write_files(self, extracted_data: Dict) -> int:
        """Write all extracted files to disk."""
        extracted_files = extracted_data.get('extracted', [])
        file_count = 0
        for file_data in extracted_files:
            try:
                filename = self._generate_filename(file_data)
                filepath = self.output_folder / filename
                content_with_header = self._build_file_content(file_data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content_with_header)
                file_count += 1
            except Exception as e:
                print(f"    Warning: Could not write {file_data.get('title', 'unknown')}: {str(e)}")
        return file_count

    def _generate_filename(self, file_data: Dict) -> str:
        """Generate filename following pattern: [COURSE-ID]_[content-type]_[sanitized-title].html"""
        course_id = file_data.get('course_id', 'UNKNOWN')
        content_type = file_data.get('type', 'content').lower()
        title = file_data.get('title', 'untitled')
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        sanitized = re.sub(r'\s+', '-', sanitized.strip()).lower()
        sanitized = sanitized[:60]
        filename = f"{course_id}_{content_type}_{sanitized}.html"
        return filename

    def _build_file_content(self, file_data: Dict) -> str:
        """Build complete file content with metadata header and body."""
        lines = []
        lines.append(f"<!-- CONTENT-TYPE: {file_data.get('type', 'Unknown').title()} -->")
        lines.append(f"<!-- COURSE: {file_data.get('course_id', 'UNKNOWN')} -->")
        if file_data.get('module'):
            lines.append(f"<!-- MODULE: {file_data['module']} -->")
        lines.append(f"<!-- TITLE: {file_data.get('title', 'Untitled')} -->")
        if file_data.get('type') in ['assignment', 'discussion', 'quiz']:
            rubric_ref = file_data.get('rubric_ref', 'NONE')
            if rubric_ref is None:
                rubric_ref = 'NONE'
            lines.append(f"<!-- RUBRIC-REF: {rubric_ref} -->")
        elif file_data.get('type') == 'rubric':
            lines.append(f"<!-- RUBRIC-NAME: {file_data.get('title', 'Unknown')} -->")
        lines.append("")
        lines.append(file_data.get('content', ''))
        return '\n'.join(lines)
