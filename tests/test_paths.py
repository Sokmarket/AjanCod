import tempfile
import unittest
from pathlib import Path
from aegis.paths import resolve_inside, PathPolicyError

class PathTests(unittest.TestCase):
    def test_path_inside(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(resolve_inside(root, "child/file.txt"), root / "child/file.txt")

    def test_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PathPolicyError):
                resolve_inside(Path(d), "../outside.txt")
if __name__ == "__main__":
    unittest.main()
