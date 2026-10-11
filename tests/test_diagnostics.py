import tempfile
import unittest
from pathlib import Path
from aegis.diagnostics import diagnose_log, inspect_workspace


class DiagnosticsTests(unittest.TestCase):
    def test_inspect_finds_syntax_error_and_marker(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "bad.py").write_text("def broken(\n    pass\n# TODO: add real validation\n", encoding="utf-8")
            result = inspect_workspace(root)
            self.assertEqual(result["status"], "FINDINGS")
            self.assertEqual(len(result["syntax_errors"]), 1)
            self.assertEqual(result["markers"][0]["marker"], "TODO")

    def test_diagnose_nameerror_suggests_scope_check(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "run.log"
            log.write_text("NameError: name 'payload' is not defined\n", encoding="utf-8")
            result = diagnose_log(log)
            self.assertEqual(result["status"], "FINDINGS")
            self.assertEqual(result["diagnoses"][0]["error_type"], "Tanımsız isim")
            self.assertIn("kapsamını", result["diagnoses"][0]["suggestion"])

    def test_diagnose_redacts_password(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "run.log"
            log.write_text("password=hunter2\nNameError: name 'x' is not defined\n", encoding="utf-8")
            result = diagnose_log(log)
            self.assertNotIn("hunter2", str(result))
if __name__ == "__main__":
    unittest.main()
