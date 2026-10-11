import tempfile
import unittest
from pathlib import Path
from aegis.report import write_reports

class ReportTests(unittest.TestCase):
    def test_reports_created_and_html_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            results = [{"task_id": "<script>", "status": "FAILED", "exit_code": 1,
                        "stdout": "", "stderr": "<bad>", "duration_seconds": 0.1}]
            json_path, html_path = write_reports(Path(d), results, "FAILED")
            self.assertTrue(json_path.is_file())
            self.assertTrue(html_path.is_file())
            text = html_path.read_text(encoding="utf-8")
            self.assertNotIn("<script>", text)
            self.assertIn("&lt;script&gt;", text)
if __name__ == "__main__":
    unittest.main()
