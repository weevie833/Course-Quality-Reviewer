"""XML parsers for IMSCC course structure, metadata, and rubrics."""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional
from html import unescape

class ModuleMetadataParser:
    """Parse course_settings/module_meta.xml for modules, items, and workflow states."""
    def __init__(self, metadata_path):
        self.metadata_path = Path(metadata_path)
        self.modules = {}
        self.items = {}
        if not self.metadata_path.exists():
            return
        try:
            self.tree = ET.parse(metadata_path)
            self.root = self.tree.getroot()
            self._parse_structure()
        except Exception as e:
            print(f"Warning: Could not parse {metadata_path}: {str(e)}")

    def _parse_structure(self):
        """Parse modules and items with their workflow states."""
        ns = {'canvas': 'http://canvas.instructure.com/xsd/cccv1p0'}
        for module_elem in self.root.findall('.//canvas:module', ns):
            module_id = module_elem.get('identifier')
            if not module_id:
                continue
            title = self._get_text(module_elem, './/canvas:title', ns)
            workflow_state = self._get_text(module_elem, './/canvas:workflow_state', ns) or 'active'
            self.modules[module_id] = {
                'identifier': module_id,
                'title': title or 'Untitled Module',
                'workflow_state': workflow_state,
                'items': []
            }
            for item_elem in module_elem.findall('.//canvas:item', ns):
                item_id = item_elem.get('identifier')
                if not item_id:
                    continue
                item_title = self._get_text(item_elem, './/canvas:title', ns)
                content_type = self._get_text(item_elem, './/canvas:content_type', ns)
                item_workflow_state = self._get_text(item_elem, './/canvas:workflow_state', ns) or 'active'
                identifierref = self._get_text(item_elem, './/canvas:identifierref', ns)
                self.items[item_id] = {
                    'identifier': item_id,
                    'title': item_title or 'Untitled',
                    'content_type': content_type,
                    'workflow_state': item_workflow_state,
                    'identifierref': identifierref,
                    'module_id': module_id
                }
                self.modules[module_id]['items'].append(item_id)

    def _get_text(self, elem, xpath, ns):
        """Helper to get text from XML element."""
        result = elem.find(xpath, ns)
        if result is not None and result.text:
            return result.text.strip()
        return None

    def is_published(self, item_id: str) -> bool:
        """Check if an item is published."""
        if item_id not in self.items:
            return True
        item = self.items[item_id]
        module_id = item.get('module_id')
        if module_id and module_id in self.modules:
            module = self.modules[module_id]
            if module['workflow_state'] != 'active':
                return False
        return item.get('workflow_state') == 'active'

    def get_module_title(self, module_id: str) -> Optional[str]:
        """Get module title by ID."""
        if module_id in self.modules:
            return self.modules[module_id]['title']
        return None

    def get_item_details(self, item_id: str) -> Optional[Dict]:
        """Get item details by ID."""
        return self.items.get(item_id)

    def get_all_modules(self) -> Dict:
        """Return all modules."""
        return self.modules

    def get_all_items(self) -> Dict:
        """Return all items."""
        return self.items


class RubricsParser:
    """Parse course_settings/rubrics.xml to extract rubric definitions."""
    def __init__(self, rubrics_path):
        self.rubrics_path = Path(rubrics_path)
        self.rubrics = {}
        if not self.rubrics_path.exists():
            return
        try:
            self.tree = ET.parse(rubrics_path)
            self.root = self.tree.getroot()
            self._parse_rubrics()
        except Exception as e:
            print(f"Warning: Could not parse {rubrics_path}: {str(e)}")

    def _parse_rubrics(self):
        """Extract rubric data from XML."""
        for rubric_elem in self.root.iter():
            if 'rubric' in rubric_elem.tag.lower():
                rubric_id = rubric_elem.get('identifier') or rubric_elem.get('id')
                if rubric_id:
                    title = self._find_title(rubric_elem)
                    self.rubrics[rubric_id] = {
                        'identifier': rubric_id,
                        'title': title or 'Untitled Rubric',
                        'content': ET.tostring(rubric_elem, encoding='unicode')
                    }

    def _find_title(self, elem):
        """Find title element within a rubric."""
        for child in elem.iter():
            if child.tag.endswith('title') or child.tag.endswith('rubric_title'):
                if child.text:
                    return child.text.strip()
        return None

    def get_rubric(self, rubric_id: str) -> Optional[Dict]:
        """Retrieve rubric by identifier."""
        return self.rubrics.get(rubric_id)

    def get_rubric_title(self, rubric_id: str) -> Optional[str]:
        """Get rubric title by ID."""
        rubric = self.rubrics.get(rubric_id)
        if rubric:
            return rubric.get('title')
        return None

    def get_all_rubrics(self) -> Dict:
        """Return all rubrics."""
        return self.rubrics
