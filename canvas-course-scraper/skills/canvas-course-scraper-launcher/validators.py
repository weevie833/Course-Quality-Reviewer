"""Validators for directory structure and folder naming."""
import re
from pathlib import Path

class DirectoryValidator:
    """Validates root directory structure."""
    def __init__(self, root_dir, imscc_dir):
        self.root_dir = Path(root_dir)
        self.imscc_dir = Path(imscc_dir)

    def validate(self):
        """Check that root directory and imscc_exports exist."""
        if not self.root_dir.exists():
            print(f"✗ Root directory not found: {self.root_dir}")
            return False
        if not self.root_dir.is_dir():
            print(f"✗ Root path is not a directory: {self.root_dir}")
            return False
        if not self.imscc_dir.exists():
            print(f"✗ imscc_exports/ directory not found at: {self.imscc_dir}")
            print(f"  Please create this folder inside your root directory.")
            return False
        return True


class NameValidator:
    """Validates course folder naming."""
    BASE_PATTERN = r'^[A-Z]{2,}\s\d{3}$'
    EXCEPTION_PATTERN = r'^[A-Z]{2,}\s\d{3}[A-Z]+$'

    def validate(self, folder_name):
        """Validate a course folder name."""
        if re.match(self.BASE_PATTERN, folder_name):
            course_id = folder_name.replace(' ', '-')
            return True, course_id, None
        if re.match(self.EXCEPTION_PATTERN, folder_name):
            response = input(f"\n  ⚠ Detected non-standard course ID '{folder_name}'. Is this intentional? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                course_id = folder_name.replace(' ', '-')
                return True, course_id, None
            else:
                issue = "Non-standard naming (user declined)"
                return False, None, issue
        issue = "Does not match pattern: 'XXX 999' (3 letters, space, 3 digits)"
        return False, None, issue
