import json
import tempfile
import unittest
from pathlib import Path
from aegis.engine import run_plan

class EngineTests(unittest.TestCase):
    def test_run_plan_executes_dependencies_before_dependent_tasks(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            workspace = root / "workspace"
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps({"schema_version": 1, "tasks": [
                {"id": "compile", "type": "python_compile", "path": "src/example.py", "depends_on": ["write"]},
                {"id": "write", "type": "write_text", "path": "src/example.py", "content": "value = 42\n"}
            ]}), encoding="utf-8")
            status, results = run_plan(plan_path, workspace)
            self.assertEqual(status, "PASSED")
            self.assertEqual([r["task_id"] for r in results], ["write", "compile"])
            self.assertTrue((workspace / "src/example.py").is_file())
            state = json.loads((workspace / ".aegis/state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "PASSED")
            self.assertEqual(state["task_status"]["compile"], "PASSED")
            events = [json.loads(line) for line in (workspace / ".aegis/events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(events[0]["event"], "run_started")
            self.assertEqual(events[-1]["event"], "run_finished")
if __name__ == "__main__":
    unittest.main()
