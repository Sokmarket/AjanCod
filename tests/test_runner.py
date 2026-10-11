import tempfile
import unittest
from pathlib import Path
from aegis.runner import Runner

class RunnerTests(unittest.TestCase):
    def test_write_text_and_compile(self):
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(Path(d))
            result = runner.execute({"id": "write", "type": "write_text", "path": "src/a.py", "content": "x = 1\n"})
            self.assertEqual(result.status, "PASSED")
            result = runner.execute({"id": "compile", "type": "python_compile", "path": "src/a.py"})
            self.assertEqual(result.status, "PASSED")

    def test_rejects_workspace_escape(self):
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(Path(d) / "workspace")
            result = runner.execute({"id": "write", "type": "write_text", "path": "../outside.txt", "content": "bad"})
            self.assertEqual(result.status, "BLOCKED")
if __name__ == "__main__":
    unittest.main()
