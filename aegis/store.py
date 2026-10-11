"""Persistent run state and append-only JSONL event log."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from aegis.security import redact_object


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStore:
    def __init__(self, workspace: Path):
        self.workspace = workspace.expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.state_dir = self.workspace / ".aegis"
        if self.state_dir.is_symlink():
            raise OSError("Refusing symlinked .aegis state directory")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.state_dir / "events.jsonl"
        self.state_path = self.state_dir / "state.json"
        if self.events_path.is_symlink() or self.state_path.is_symlink():
            raise OSError("Refusing symlinked AEGIS state files")

    def append_event(self, event: dict) -> None:
        if self.events_path.is_symlink():
            raise OSError("Refusing symlinked event log")
        record = redact_object({**event, "timestamp": utc_now()})
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()

    def save_state(self, state: dict) -> None:
        if self.state_path.is_symlink():
            raise OSError("Refusing symlinked state file")
        fd, temp_name = tempfile.mkstemp(prefix=".state.", suffix=".tmp", dir=self.state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(redact_object(state), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.state_path)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def load_state(self) -> dict | None:
        if not self.state_path.exists():
            return None
        if self.state_path.is_symlink():
            raise OSError("Refusing symlinked state file")
        return json.loads(self.state_path.read_text(encoding="utf-8"))
