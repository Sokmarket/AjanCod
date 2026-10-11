"""Explicit per-workspace privacy permissions."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def permission_path(workspace: Path) -> Path:
    return workspace.expanduser().resolve() / ".aegis" / "screen-permission.json"


def get_screen_permission(workspace: Path) -> dict:
    root = workspace.expanduser().resolve()
    state_dir = root / ".aegis"
    path = permission_path(root)
    if state_dir.is_symlink() or path.is_symlink() or not path.is_file():
        return {"enabled": False, "granted_at": None}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return {"enabled": value.get("enabled") is True, "granted_at": value.get("granted_at")}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"enabled": False, "granted_at": None}


def set_screen_permission(workspace: Path, enabled: bool) -> dict:
    root = workspace.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = permission_path(root)
    # A symlinked permission directory/file could redirect a privacy setting.
    current = root
    for part in (".aegis", "screen-permission.json"):
        current = current / part
        if current.is_symlink():
            raise ValueError("Screen permission path cannot contain symlinks")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "enabled": bool(enabled),
               "granted_at": datetime.now(timezone.utc).isoformat() if enabled else None}
    fd, tmp = tempfile.mkstemp(prefix=".screen-permission.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return {"enabled": bool(enabled), "granted_at": payload["granted_at"]}
