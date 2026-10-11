import tempfile
import unittest
from pathlib import Path
from aegis.agent import collect_context

class AgentContextTests(unittest.TestCase):
    def test_context_includes_text_and_skips_symlinked_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "main.py").write_text("print('hello')", encoding="utf-8")
            (root / ".env").write_text("API_KEY=not-for-model-context", encoding="utf-8")
            (root / "service-secret.json").write_text("SECRET=not-for-model-context", encoding="utf-8")
            outside = root.parent / "aegis-context-outside.txt"
            outside.write_text("SHOULD_NOT_APPEAR", encoding="utf-8")
            try:
                (root / "leak.py").symlink_to(outside)
                context = collect_context(root)
                self.assertIn("main.py", context)
                self.assertNotIn("SHOULD_NOT_APPEAR", context)
                self.assertNotIn("not-for-model-context", context)
            finally:
                outside.unlink(missing_ok=True)
if __name__ == "__main__":
    unittest.main()
