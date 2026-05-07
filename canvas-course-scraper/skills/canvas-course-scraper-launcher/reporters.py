"""Extraction report generator — creates summary of extracted vs. ignored content."""
from typing import Dict

class ExtractionReporter:
    """Generates extraction reports showing what was extracted and what was ignored."""
    def __init__(self, course_id, extracted_data):
        self.course_id = course_id
        self.extracted_data = extracted_data

    def generate_report(self) -> str:
        """Generate extraction report as text."""
        extracted = self.extracted_data.get('extracted', [])
        ignored = self.extracted_data.get('ignored', [])
        lines = []
        lines.append(f"{self.course_id} Extraction Report")
        lines.append("=" * 70)
        lines.append("")
        total_items = len(extracted) + len(ignored)
        lines.append(f"Total items found: {total_items}")
        lines.append("")
        lines.append(f"EXTRACTED ({len(extracted)} files):")
        for item in sorted(extracted, key=lambda x: (x.get('type', 'z'), x.get('title', ''))):
            item_type = item.get('type', 'unknown').title()
            title = item.get('title', 'Untitled')
            lines.append(f"  - {item_type}: {title}")
        lines.append("")
        lines.append(f"IGNORED ({len(ignored)} items):")
        for item in sorted(ignored, key=lambda x: (x.get('type', 'z'), x.get('title', ''))):
            title = item.get('title', 'Untitled')
            lines.append(f"  - {title}")
        lines.append("")
        lines.append("=" * 70)
        lines.append("\nAfter review, if you'd like to extract any ignored items,")
        lines.append("re-run the scraper and use the override prompt.")
        lines.append("")
        return '\n'.join(lines)
