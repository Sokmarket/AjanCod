import tempfile
import unittest
from pathlib import Path
from aegis.watch import python_snapshot, watch_workspace


class WatchTests(unittest.TestCase):
    def test_snapshot_tracks_python_file_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "main.py"
            source.write_text("x = 1\n", encoding="utf-8")
            first = python_snapshot(root)
            source.write_text("x = 200\n", encoding="utf-8")
            second = python_snapshot(root)
            self.assertIn("main.py", first)
            self.assertNotEqual(first["main.py"], second["main.py"])

    def test_watch_emits_initial_scan_in_bounded_mode(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "main.py").write_text("x = 1\n", encoding="utf-8")
            results = []
            watch_workspace(root, interval=1, callback=lambda report, changed: results.append((report, changed)), max_checks=1)
            self.assertEqual(len(results), 1)
            self.assertFalse(results[0][1])
            self.assertEqual(results[0][0]["status"], "PASSED")
if __name__ == "__main__":
    unittest.main()
