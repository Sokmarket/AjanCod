from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class TaskResult:
    task_id: str
    status: str
    command_name: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
