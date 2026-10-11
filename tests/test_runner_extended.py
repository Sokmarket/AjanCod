import tempfile
import unittest
import sys
from pathlib import Path
from aegis.runner import Runner


class RunnerExtendedTests(unittest.TestCase):
    def test_malformed_task_returns_blocked_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            result = Runner(Path(d)).execute({"type": "write_text"})
            self.assertEqual(result.status, "BLOCKED")

    def test_symlink_write_target_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "real").mkdir()
            try:
                (root / "link").symlink_to(root / "real", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable on this environment")
            result = Runner(root).execute({"id": "write", "type": "write_text", "path": "link/out.txt", "content": "unsafe"})
            self.assertEqual(result.status, "BLOCKED")
            self.assertFalse((root / "real/out.txt").exists())

    def test_compile_does_not_create_bytecode_cache(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "src" / "sample.py"
            source.parent.mkdir()
            source.write_text("value = 1\n", encoding="utf-8")
            result = Runner(root).execute({"id": "compile", "type": "python_compile", "path": "src/sample.py"})
            self.assertEqual(result.status, "PASSED")
            self.assertFalse((source.parent / "__pycache__").exists())

    def test_runner_blocks_reserved_and_sensitive_write_paths(self):
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(Path(d))
            for path in (".aegis/state.json", ".env", "credentials.json", "private-key.pem"):
                result = runner.execute({"id": "write", "type": "write_text", "path": path, "content": "bad"})
                self.assertEqual(result.status, "BLOCKED", path)

    def test_output_capture_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(Path(d), timeout_seconds=10)
            completed = runner._run([sys.executable, "-I", "-c", "import sys; sys.stdout.write('x' * 300000)"])
            self.assertEqual(completed.returncode, 0)
            self.assertLessEqual(len(completed.stdout), 20000)

    def test_timeout_returns_failed_result(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            test_file = root / "test_slow.py"
            test_file.write_text("import time\nimport unittest\nclass Slow(unittest.TestCase):\n def test_slow(self): time.sleep(4)\n", encoding="utf-8")
            result = Runner(root, timeout_seconds=1).execute({"id": "tests", "type": "python_unittest", "path": "test_slow.py"})
            self.assertEqual(result.status, "FAILED")
            self.assertEqual(result.error, "TIMEOUT")
if __name__ == "__main__":
    unittest.main()
