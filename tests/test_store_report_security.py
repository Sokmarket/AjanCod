import tempfile
import json
import unittest
from pathlib import Path
from aegis.paths import PathPolicyError
from aegis.report import write_reports
from aegis.store import ProjectStore


class StoreReportSecurityTests(unittest.TestCase):
    def test_store_refuses_symlinked_state_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            workspace = root / "workspace"
            workspace.mkdir()
            other = root / "elsewhere"
            other.mkdir()
            try:
                (workspace / ".aegis").symlink_to(other, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable on this environment")
            with self.assertRaises(OSError):
                ProjectStore(workspace)

    def test_event_log_redacts_inline_passwords(self):
        with tempfile.TemporaryDirectory() as d:
            workspace = Path(d)
            store = ProjectStore(workspace)
            store.append_event({"event": "task_finished", "stdout": "password=hunter2"})
            record = json.loads((workspace / ".aegis/events.jsonl").read_text(encoding="utf-8"))
            self.assertNotIn("hunter2", record["stdout"])
            self.assertIn("[REDACTED]", record["stdout"])

    def test_report_refuses_symlinked_reports_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            workspace = root / "workspace"
            workspace.mkdir()
            other = root / "outside"
            other.mkdir()
            try:
                (workspace / "reports").symlink_to(other, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable on this environment")
            with self.assertRaises(PathPolicyError):
                write_reports(workspace, [], "PASSED")
            self.assertEqual(list(other.iterdir()), [])
if __name__ == "__main__":
    unittest.main()
