import unittest
from aegis.plan import validate_plan, ordered_tasks, PlanError

class PlanTests(unittest.TestCase):
    def test_valid_plan(self):
        validate_plan({"schema_version": 1, "tasks": [
            {"id": "a", "type": "write_text", "path": "x.txt", "content": "x"},
            {"id": "b", "type": "python_compile", "path": "x.py", "depends_on": ["a"]}
        ]})

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(PlanError):
            validate_plan({"schema_version": 1, "tasks": [
                {"id": "x", "type": "write_text", "path": "x", "content": "x"},
                {"id": "x", "type": "write_text", "path": "y", "content": "y"}
            ]})

    def test_cycle_rejected(self):
        with self.assertRaises(PlanError):
            validate_plan({"schema_version": 1, "tasks": [
                {"id": "a", "type": "write_text", "path": "a", "content": "", "depends_on": ["b"]},
                {"id": "b", "type": "write_text", "path": "b", "content": "", "depends_on": ["a"]}
            ]})

    def test_out_of_order_dependencies_are_sorted(self):
        plan = {"schema_version": 1, "tasks": [
            {"id": "second", "type": "python_compile", "path": "x.py", "depends_on": ["first"]},
            {"id": "first", "type": "write_text", "path": "x.py", "content": "x = 1"},
        ]}
        self.assertEqual([t["id"] for t in ordered_tasks(plan)], ["first", "second"])

    def test_bool_is_not_schema_version_one(self):
        with self.assertRaises(PlanError):
            validate_plan({"schema_version": True, "tasks": [
                {"id": "a", "type": "write_text", "path": "a", "content": "x"}
            ]})

    def test_unknown_fields_rejected(self):
        with self.assertRaises(PlanError):
            validate_plan({"schema_version": 1, "tasks": [
                {"id": "a", "type": "write_text", "path": "a", "content": "x", "shell": True}
            ]})

    def test_workspace_path_traversal_rejected_during_plan_validation(self):
        plan = {"schema_version": 1, "tasks": [{"id": "x", "type": "write_text", "path": "../outside.txt", "content": "x"}]}
        with self.assertRaises(PlanError):
            validate_plan(plan)

    def test_write_content_limit_is_enforced(self):
        from aegis.plan import MAX_CONTENT_BYTES
        plan = {"schema_version": 1, "tasks": [{"id": "x", "type": "write_text", "path": "x.txt", "content": "x" * (MAX_CONTENT_BYTES + 1)}]}
        with self.assertRaises(PlanError):
            validate_plan(plan)
if __name__ == "__main__":
    unittest.main()
