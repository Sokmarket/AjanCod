"""Strict validation and stable dependency ordering for AEGIS task plans."""
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

MAX_PLAN_BYTES = 5_000_000
MAX_TASKS = 500
MAX_PATH_CHARS = 512
MAX_CONTENT_BYTES = 1_000_000
ALLOWED_TASK_TYPES = {"python_compile", "python_unittest", "write_text"}
TASK_FIELDS = {
    "write_text": {"id", "type", "path", "content", "depends_on"},
    "python_compile": {"id", "type", "path", "depends_on"},
    "python_unittest": {"id", "type", "path", "depends_on"},
}


class PlanError(ValueError):
    """Raised when a task plan is malformed or unsafe to execute."""


def load_plan(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_PLAN_BYTES:
            raise PlanError(f"Plan exceeds {MAX_PLAN_BYTES} bytes")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"Cannot read valid JSON plan: {exc}") from exc
    validate_plan(data)
    return data


def validate_plan(data: object) -> None:
    if not isinstance(data, dict):
        raise PlanError("Plan root must be an object")
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        raise PlanError("schema_version must be integer 1")
    if set(data) != {"schema_version", "tasks"}:
        raise PlanError("Plan may contain only schema_version and tasks")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise PlanError("tasks must be a non-empty list")
    if len(tasks) > MAX_TASKS:
        raise PlanError(f"Plan has too many tasks (max {MAX_TASKS})")

    by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise PlanError("Each task must be an object")
        task_id, kind = task.get("id"), task.get("type")
        if not isinstance(task_id, str) or not task_id.strip() or task_id != task_id.strip():
            raise PlanError("Each task needs a non-empty id without surrounding whitespace")
        if task_id in by_id:
            raise PlanError(f"Duplicate task id: {task_id}")
        if not isinstance(kind, str) or kind not in ALLOWED_TASK_TYPES:
            raise PlanError(f"Unsupported task type: {kind}")
        unknown = set(task) - TASK_FIELDS[kind]
        if unknown:
            raise PlanError(f"Unsupported field(s) in task {task_id}: {sorted(unknown)}")
        path = task.get("path")
        if not isinstance(path, str) or not path.strip():
            raise PlanError(f"Task {task_id} requires a non-empty path")
        if len(path) > MAX_PATH_CHARS or "\x00" in path or "\\" in path:
            raise PlanError(f"Task {task_id} path contains unsupported characters or is too long")
        try:
            path.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise PlanError(f"Task {task_id} path contains invalid Unicode") from exc
        pure_path = PurePosixPath(path)
        if pure_path.is_absolute() or ".." in pure_path.parts or re.match(r"^[A-Za-z]:", path):
            raise PlanError(f"Task {task_id} path must be workspace-relative and contain no '..' segments")
        if kind == "write_text":
            if not isinstance(task.get("content"), str):
                raise PlanError(f"Task {task_id} requires string content")
            try:
                content_size = len(task["content"].encode("utf-8"))
            except UnicodeEncodeError as exc:
                raise PlanError(f"Task {task_id} content contains invalid Unicode") from exc
            if content_size > MAX_CONTENT_BYTES:
                raise PlanError(f"Task {task_id} content exceeds {MAX_CONTENT_BYTES} bytes")
        deps = task.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(dep, str) and dep.strip() for dep in deps):
            raise PlanError(f"depends_on must be a list of non-empty task ids: {task_id}")
        if len(deps) != len(set(deps)):
            raise PlanError(f"Duplicate dependency in task {task_id}")
        if task_id in deps:
            raise PlanError(f"Task cannot depend on itself: {task_id}")
        by_id[task_id] = task

    for task in tasks:
        for dep in task.get("depends_on", []):
            if dep not in by_id:
                raise PlanError(f"Unknown dependency {dep!r} in task {task['id']}")

    # Detect cycles with DFS; execute_plan() separately computes stable topological order.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise PlanError(f"Dependency cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dep in by_id[node].get("depends_on", []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for task_id in by_id:
        visit(task_id)


def ordered_tasks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a stable topological ordering; unrelated tasks retain input order."""
    validate_plan(plan)
    tasks = plan["tasks"]
    by_id = {task["id"]: task for task in tasks}
    completed: set[str] = set()
    ordered: list[dict[str, Any]] = []
    while len(ordered) < len(tasks):
        ready = [task for task in tasks
                 if task["id"] not in completed
                 and all(dep in completed for dep in task.get("depends_on", []))]
        if not ready:  # Defensive; validation should already detect cycles.
            raise PlanError("No executable task found; dependency graph is invalid")
        task = ready[0]
        ordered.append(task)
        completed.add(task["id"])
    return ordered
