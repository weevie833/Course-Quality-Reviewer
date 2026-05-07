"""
Content extractors for pages, assignments, discussions, quizzes, and rubrics.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from html import unescape
from typing import List, Dict, Optional


class CourseContentExtractor:
    """Extract all course content: pages, assignments, discussions, quizzes, rubrics."""

    # Excluded page titles (exact matches)
    EXCLUDED_PAGE_TITLES = {
        'Ongoing Instructor Notes for Future Reference',
        'About the Use of AI in This Course',
        'About Your Instructor',
        'Course Resources',
        'Home CPSO',
    }

    # Excluded page titles (contains match)
    EXCLUDED_PAGE_CONTAINS = [
        'Faculty Quick Guides',
        'Getting Started: Canvas Resources',
        'Rubric',
    ]

    def __init__(self, course_folder, metadata_parser, rubrics_parser, course_id, course_title, manifest_path=None):
        self.course_folder = Path(course_folder)
        self.metadata_parser = metadata_parser
        self.rubrics_parser = rubrics_parser
        self.course_id = course_id
        self.course_title = course_title
        self.manifest_path = manifest_path
        self.extracted_files = []
        self.ignored_items = []
        self.discussion_settings_map = {}  # Maps discussion content file IDs to settings file paths
        self._build_discussion_settings_map()

    def _build_discussion_settings_map(self):
        """Parse manifest to map discussion content file IDs to settings file GUIDs.

        Discussions exist as pairs linked via manifest:
        - imsdt_xmlv1p1 resource (content) with dependency on associatedcontent resource (settings)
        - The dependency element has identifierref pointing to the settings resource

        Builds mapping: {content_resource_id → (content_href, settings_resource_id)}.
        """
        if not self.manifest_path or not self.manifest_path.exists():
            return

        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()

            # Resources can be namespaced or not
            resources = {}
            for resource in root.iter():
                if resource.tag.endswith('resource'):
                    res_id = resource.get('identifier', '')
                    if res_id:
                        resources[res_id] = {
                            'type': resource.get('type', ''),
                            'href': resource.get('href', ''),
                            'file_elem': None,
                            'dependencies': []
                        }
                        # Get file href if present
                        for file_elem in resource.iter():
                            if file_elem.tag.endswith('file'):
                                resources[res_id]['file_elem'] = file_elem.get('href', '')
                                break
                        # Get dependencies
                        for dep_elem in resource.iter():
                            if dep_elem.tag.endswith('dependency'):
                                dep_ref = dep_elem.get('identifierref', '')
                                if dep_ref:
                                    resources[res_id]['dependencies'].append(dep_ref)

            # Now link imsdt content files to their settings files (associatedcontent)
            for resource_id, resource_info in resources.items():
                if 'imsdt_xmlv1p1' in resource_info['type']:
                    # This is a discussion content file
                    content_href = resource_info['file_elem'] or ''
                    if not content_href:
                        continue

                    # Look for dependent settings resource (associatedcontent)
                    for dep_ref in resource_info['dependencies']:
                        if dep_ref in resources:
                            dep_info = resources[dep_ref]
                            if 'associatedcontent/imscc_xmlv1p1' in dep_info['type']:
                                # Found the settings file reference
                                settings_href = dep_info['file_elem'] or ''
                                self.discussion_settings_map[content_href] = (settings_href, dep_ref)
                                break

        except Exception as e:
            pass  # Silently fail if manifest parsing doesn't work

    def extract_all(self) -> Dict:
        """Execute full extraction pipeline."""
        self._extract_pages()
        self._extract_assignments()
        self._extract_discussions()
        self._extract_rubrics()

        return {
            'extracted': self.extracted_files,
            'ignored': self.ignored_items
        }

    def _extract_pages(self):
        """Extract published pages from wiki_content/."""
        wiki_dir = self.course_folder / "wiki_content"
        if not wiki_dir.exists():
            return

        for html_file in sorted(wiki_dir.glob("*.html")):
            try:
                page_title = html_file.stem
                readable_title = page_title.replace('-', ' ').title()

                # Apply exclusion rules
                if self._should_exclude_page(page_title, readable_title):
                    self.ignored_items.append({'type': 'page', 'title': readable_title})
                    continue

                # Check if published
                if self.metadata_parser:
                    is_published = False
                    for item_id, item in self.metadata_parser.get_all_items().items():
                        if self._titles_match(item.get('title'), readable_title) and item.get('content_type') == 'WikiPage':
                            is_published = self.metadata_parser.is_published(item_id)
                            break
                    if not is_published:
                        self.ignored_items.append({'type': 'page', 'title': readable_title})
                        continue

                content = html_file.read_text(encoding='utf-8')
                module_title = self._find_module_for_item(readable_title)

                self.extracted_files.append({
                    'type': 'page',
                    'title': readable_title,
                    'content': content,
                    'course_id': self.course_id,
                    'module': module_title,
                })

            except Exception as e:
                print(f"      Warning: Could not extract page {html_file.name}: {str(e)}")

    def _extract_assignments(self):
        """Extract assignments from [guid]/assignment_settings.xml."""
        if not self.metadata_parser:
            return

        # Find all assignment_settings.xml files
        for settings_file in self.course_folder.rglob("assignment_settings.xml"):
            try:
                guid_folder = settings_file.parent

                # Parse assignment settings
                tree = ET.parse(settings_file)
                root = tree.getroot()

                # Handle namespaced elements
                ns = {'canvas': 'http://canvas.instructure.com/xsd/cccv1p0'}
                
                # Get title - try with full namespace first
                title_text = None
                for elem in root:
                    if elem.tag.endswith('title'):
                        title_text = elem.text
                        break
                
                assignment_title = title_text.strip() if title_text else "Untitled Assignment"

                # Get workflow state
                workflow_text = None
                for elem in root:
                    if elem.tag.endswith('workflow_state'):
                        workflow_text = elem.text
                        break
                
                workflow_state = workflow_text if workflow_text else 'published'

                # Check if published
                if workflow_state != 'published':
                    self.ignored_items.append({'type': 'assignment', 'title': assignment_title})
                    continue

                # Look for HTML content file
                html_file = None
                for html in guid_folder.glob("*.html"):
                    html_file = html
                    break

                if not html_file:
                    self.ignored_items.append({'type': 'assignment', 'title': assignment_title})
                    continue

                content = html_file.read_text(encoding='utf-8')

                # Extract rubric reference
                rubric_ref = 'NONE'
                for elem in root:
                    if elem.tag.endswith('rubric_identifierref') and elem.text:
                        rubric_id = elem.text
                        if self.rubrics_parser:
                            rubric_title = self.rubrics_parser.get_rubric_title(rubric_id)
                            rubric_ref = rubric_title if rubric_title else 'UNRESOLVED'
                        else:
                            rubric_ref = 'UNRESOLVED'
                        break

                module_title = self._find_module_for_item(assignment_title)

                self.extracted_files.append({
                    'type': 'assignment',
                    'title': assignment_title,
                    'content': content,
                    'course_id': self.course_id,
                    'module': module_title,
                    'rubric_ref': rubric_ref,
                })

            except Exception as e:
                print(f"      Warning: Could not extract assignment from {settings_file.parent.name}: {str(e)}")

    def _extract_discussions(self):
        """Extract discussions from .xml files (imsdt format).

        Discussions are paired files:
        - Content file: g[guid].xml (imsdt_xmlv1p1, contains text)
        - Settings file: g[guid].xml (topicMeta, contains rubric reference)

        Only extracts discussions that have a rubric_identifierref in settings file.
        """
        if not self.metadata_parser:
            return

        # Find all discussion XML files (imsdt_xmlv1p1 format)
        for xml_file in self.course_folder.glob("*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Check if this is a discussion (has <topic> with <text> element)
                if not root.tag.endswith('topic'):
                    continue

                # Extract title - use iteration to handle namespaces
                discussion_title = None
                for elem in root.iter():
                    if elem.tag.endswith('title'):
                        if elem.text:
                            discussion_title = elem.text.strip()
                        break

                if not discussion_title:
                    continue

                # Apply discussion filtering rules
                if self._should_exclude_discussion(discussion_title):
                    self.ignored_items.append({'type': 'discussion', 'title': discussion_title})
                    continue

                # Check if published via metadata
                is_published = False
                if self.metadata_parser:
                    for item_id, item in self.metadata_parser.get_all_items().items():
                        if (self._titles_match(item.get('title'), discussion_title) and
                            item.get('content_type') == 'DiscussionTopic'):
                            is_published = self.metadata_parser.is_published(item_id)
                            break
                if not is_published:
                    self.ignored_items.append({'type': 'discussion', 'title': discussion_title})
                    continue

                # Extract HTML content - use iteration to handle namespaces
                content = None
                for elem in root.iter():
                    if elem.tag.endswith('text'):
                        if elem.text:
                            content = unescape(elem.text)
                        break

                if not content:
                    self.ignored_items.append({'type': 'discussion', 'title': discussion_title})
                    continue

                # Extract rubric reference from settings file
                rubric_ref = self._extract_discussion_rubric(xml_file)

                # Only extract discussions that have a rubric (are assessed)
                if rubric_ref == 'NONE':
                    self.ignored_items.append({'type': 'discussion', 'title': discussion_title})
                    continue

                module_title = self._find_module_for_item(discussion_title)

                self.extracted_files.append({
                    'type': 'discussion',
                    'title': discussion_title,
                    'content': content,
                    'course_id': self.course_id,
                    'module': module_title,
                    'rubric_ref': rubric_ref,
                })

            except Exception as e:
                pass  # Skip silently if not a valid discussion

    def _extract_discussion_rubric(self, content_xml_file: Path) -> str:
        """Extract rubric reference from discussion settings file.

        Given a discussion content file (imsdt), find its paired settings file
        (topicMeta) using the manifest mapping and extract the rubric_identifierref
        from the nested assignment.

        Returns:
        - Rubric title (resolved from rubric ID)
        - 'UNRESOLVED' if rubric reference exists but can't be resolved
        - 'NONE' if no rubric reference found
        """
        try:
            # Get just the filename (href) for lookup
            content_href = content_xml_file.name

            # Check if we have a mapping for this file
            if content_href not in self.discussion_settings_map:
                return 'NONE'

            # Get the settings file href and resource ID from the mapping
            settings_href, settings_resource_id = self.discussion_settings_map[content_href]

            # Build path to settings file
            settings_file = self.course_folder / settings_href

            if not settings_file.exists():
                return 'NONE'

            # Parse settings file and extract rubric reference
            tree = ET.parse(settings_file)
            root = tree.getroot()

            # Look for assignment element with rubric_identifierref
            # The structure is: <topicMeta><assignment><rubric_identifierref>
            for elem in root.iter():
                if elem.tag.endswith('rubric_identifierref') and elem.text:
                    rubric_id = elem.text.strip()
                    if self.rubrics_parser:
                        rubric_title = self.rubrics_parser.get_rubric_title(rubric_id)
                        return rubric_title if rubric_title else 'UNRESOLVED'
                    else:
                        return 'UNRESOLVED'

            return 'NONE'

        except Exception as e:
            return 'NONE'

    def _extract_rubrics(self):
        """Extract all rubrics."""
        if not self.rubrics_parser:
            return

        for rubric_id, rubric_data in self.rubrics_parser.get_all_rubrics().items():
            try:
                self.extracted_files.append({
                    'type': 'rubric',
                    'title': rubric_data.get('title', 'Untitled Rubric'),
                    'content': rubric_data.get('content', ''),
                    'course_id': self.course_id,
                    'rubric_id': rubric_id,
                })
            except Exception as e:
                print(f"      Warning: Could not extract rubric {rubric_id}: {str(e)}")

    def _should_exclude_page(self, filename: str, title: str) -> bool:
        """Check if page should be excluded."""
        if title in self.EXCLUDED_PAGE_TITLES:
            return True
        title_lower = title.lower()
        for excluded in self.EXCLUDED_PAGE_CONTAINS:
            if excluded.lower() in title_lower:
                return True
        return False

    def _should_exclude_discussion(self, title: str) -> bool:
        """Check if discussion should be excluded."""
        # Exclude discussions with "Introduction" in title
        if 'introduction' in title.lower():
            return True
        # Exclude "General Q & A"
        if title.strip().lower() == 'general q & a':
            return True
        return False

    def _titles_match(self, item_title: str, page_title: str) -> bool:
        """Check if titles match (case-insensitive)."""
        if not item_title or not page_title:
            return False
        return item_title.strip().lower() == page_title.strip().lower()

    def _find_module_for_item(self, item_title: str) -> str:
        """Find the module containing this item."""
        if not self.metadata_parser:
            return 'Unknown Module'

        for item_id, item in self.metadata_parser.get_all_items().items():
            if self._titles_match(item.get('title'), item_title):
                module_id = item.get('module_id')
                if module_id:
                    module = self.metadata_parser.modules.get(module_id)
                    if module:
                        return module['title']

        return 'Unknown Module'
