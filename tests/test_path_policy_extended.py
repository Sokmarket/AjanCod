import tempfile
import unittest
from pathlib import Path
from aegis.paths import PathPolicyError, resolve_inside


class ExtendedPathPolicyTests(unittest.TestCase):
    def test_rejects_symlink_even_when_target_is_inside_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "real").mkdir()
            (root / "real/file.txt").write_text("safe", encoding="utf-8")
            try:
                (root / "link").symlink_to(root / "real", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable on this environment")
            with self.assertRaises(PathPolicyError):
                resolve_inside(root, "link/file.txt")
if __name__ == "__main__":
    unittest.main()
