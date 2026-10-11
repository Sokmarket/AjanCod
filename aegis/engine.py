from pathlib import Path
from datetime import datetime, timezone
from aegis.plan import load_plan, ordered_tasks
from aegis.runner import Runner
from aegis.store import ProjectStore
from aegis.report import write_reports

def run_plan(plan_path: Path, workspace: Path) -> tuple[str, list[dict]]:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    plan = load_plan(plan_path)
    runner, store = Runner(workspace), ProjectStore(workspace)
    started_at = datetime.now(timezone.utc).isoformat()
    store.save_state({"status": "RUNNING", "plan": str(plan_path.resolve()), "started_at": started_at, "task_status": {}, "results": []})
    store.append_event({"event": "run_started", "plan": str(plan_path.resolve()), "task_count": len(plan["tasks"])})
    results, status_by_id = [], {}
    for task in ordered_tasks(plan):
        blocked_deps = [dep for dep in task.get("depends_on", [])
                        if status_by_id.get(dep) != "PASSED"]
        if blocked_deps:
            result = {
                "task_id": task["id"], "status": "BLOCKED", "command_name": task["type"],
                "exit_code": None, "stdout": "", "stderr": "", "duration_seconds": 0.0,
                "error": f"Dependencies not passed: {blocked_deps}"
            }
        else:
            store.append_event({"event": "task_started", "task_id": task["id"]})
            result = runner.execute(task).to_dict()
        results.append(result)
        status_by_id[task["id"]] = result["status"]
        store.append_event({"event": "task_finished", **result})
        store.save_state({"status": "RUNNING", "plan": str(plan_path.resolve()), "started_at": started_at,
                          "last_task_id": task["id"], "task_status": status_by_id, "results": results})
    overall = "PASSED" if results and all(x["status"] == "PASSED" for x in results) else "FAILED"
    json_path, html_path = write_reports(workspace, results, overall)
    finished_at = datetime.now(timezone.utc).isoformat()
    store.append_event({"event": "run_finished", "status": overall,
                        "json_report": str(json_path), "html_report": str(html_path)})
    store.save_state({"status": overall, "plan": str(plan_path.resolve()), "started_at": started_at,
                      "finished_at": finished_at, "task_status": status_by_id, "results": results,
                      "json_report": str(json_path), "html_report": str(html_path)})
    return overall, results
