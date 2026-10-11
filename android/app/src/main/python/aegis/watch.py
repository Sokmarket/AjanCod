"""On-demand workspace watcher; no background service is installed."""
import os
import time
from pathlib import Path
from typing import Callable
from aegis.diagnostics import inspect_workspace

IGNORE_DIRS = {".git", ".aegis", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "coverage", "reports"}


def python_snapshot(workspace: Path) -> dict[str, tuple[int, int]]:
    root = workspace.expanduser().resolve()
    if not root.is_dir():
        raise OSError(f"Workspace does not exist: {root}")
    snapshot: dict[str, tuple[int, int]] = {}
    for current, dirs, filenames in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not (Path(current) / d).is_symlink())
        for name in sorted(filenames):
            path = Path(current) / name
            if path.suffix != ".py" or path.is_symlink():
                continue
            try:
                stat = path.stat()
                snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                continue
    return snapshot


def watch_workspace(workspace: Path, interval: float = 5.0,
                    callback: Callable[[dict, bool], None] | None = None,
                    max_checks: int | None = None) -> None:
    """Poll Python file metadata and emit a fresh inspection after changes.

    max_checks exists for bounded tests / embedding; normal CLI use stops with Ctrl+C.
    """
    delay = max(1.0, min(float(interval), 60.0))
    previous = None
    checks = 0
    root = workspace.expanduser().resolve()
    while max_checks is None or checks < max_checks:
        current = python_snapshot(root)
        changed = previous is None or current != previous
        if changed:
            report = inspect_workspace(root)
            if callback:
                callback(report, previous is not None)
        previous = current
        checks += 1
        if max_checks is None or checks < max_checks:
            time.sleep(delay)
