import tempfile
import unittest
from pathlib import Path
from aegis.permissions import get_screen_permission, set_screen_permission
from aegis.screen import analyze_screen


class PermissionScreenTests(unittest.TestCase):
    def test_screen_permission_defaults_to_disabled_and_can_revoke(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "workspace"
            root.mkdir()
            self.assertFalse(get_screen_permission(root)["enabled"])
            self.assertTrue(set_screen_permission(root, True)["enabled"])
            self.assertTrue(get_screen_permission(root)["enabled"])
            self.assertFalse(set_screen_permission(root, False)["enabled"])
            self.assertFalse(get_screen_permission(root)["enabled"])

    def test_screen_analysis_never_captures_without_permission(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(PermissionError):
                analyze_screen(root, confirmed=True)

    def test_screen_analysis_requires_per_capture_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            set_screen_permission(root, True)
            with self.assertRaises(PermissionError):
                analyze_screen(root, confirmed=False)
if __name__ == "__main__":
    unittest.main()
