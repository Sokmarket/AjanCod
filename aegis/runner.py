"""Allowlisted task runner. This is not an OS-level security sandbox."""
import os
import signal
import subprocess
import sys
import time
import tempfile
import threading
from pathlib import Path, PurePosixPath
from aegis.models import TaskResult
from aegis.paths import resolve_inside
from aegis.security import redact_secrets

MAX_OUTPUT_CHARS = 20000
MAX_WRITE_BYTES = 1_000_000


class Runner:
    def __init__(self, workspace: Path, timeout_seconds: int = 30):
        self.workspace = workspace.expanduser().resolve()
        self.timeout_seconds = max(1, min(int(timeout_seconds), 300))
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Run without a shell, cap retained output in memory and kill POSIX groups on timeout."""
        env = {"PATH": os.environ.get("PATH", os.defpath), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
        process = subprocess.Popen(
            command, cwd=self.workspace, shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=False, env=env, close_fds=True,
            start_new_session=(os.name == "posix"),
        )
        tails = {"stdout": bytearray(), "stderr": bytearray()}
        max_bytes = MAX_OUTPUT_CHARS * 4

        def drain(stream, tail):
            try:
                while True:
                    chunk = stream.read(4096)
                    if not chunk:
                        break
                    tail.extend(chunk)
                    if len(tail) > max_bytes:
                        del tail[:len(tail) - max_bytes]
            finally:
                stream.close()

        readers = [threading.Thread(target=drain, args=(process.stdout, tails["stdout"]), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, tails["stderr"]), daemon=True)]
        for thread in readers:
            thread.start()

        def decoded(name):
            return tails[name].decode("utf-8", errors="replace")[-MAX_OUTPUT_CHARS:]

        try:
            process.wait(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.wait()
            for thread in readers:
                thread.join(timeout=2)
            raise subprocess.TimeoutExpired(command, self.timeout_seconds, output=decoded("stdout"), stderr=decoded("stderr"))
        for thread in readers:
            thread.join()
        return subprocess.CompletedProcess(command, process.returncode, decoded("stdout"), decoded("stderr"))

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, target)
        except Exception:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise

    def execute(self, task: dict) -> TaskResult:
        task_id = task.get("id", "<unknown>") if isinstance(task, dict) else "<unknown>"
        kind = task.get("type", "<unknown>") if isinstance(task, dict) else "<unknown>"
        started = time.monotonic()
        try:
            if not isinstance(task, dict) or not isinstance(task.get("path"), str):
                raise ValueError("Task must be an object with a string path")
            normalized_parts = PurePosixPath(task["path"].replace("\\", "/")).parts
            sensitive_markers = ("secret", "credential", "token", "password", "passwd", "private-key", "private_key", "id_rsa", "id_ed25519")
            reserved_parts = {".git", ".aegis", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", "secrets", "credentials"}
            if any(part.lower() in reserved_parts or part.lower().startswith(".env") for part in normalized_parts):
                raise ValueError("Task path targets a reserved internal/build/sensitive directory")
            filename_lower = normalized_parts[-1].lower() if normalized_parts else ""
            if filename_lower.startswith(".env") or any(marker in filename_lower for marker in sensitive_markers):
                raise ValueError("Task path appears to target a sensitive file")
            if filename_lower.endswith((".pem", ".key", ".p12", ".pfx", ".der")):
                raise ValueError("Task path targets a protected key/certificate file")
            if kind == "write_text":
                if not isinstance(task.get("content"), str):
                    raise ValueError("write_text requires string content")
                if len(task["content"].encode("utf-8")) > MAX_WRITE_BYTES:
                    raise ValueError(f"write_text exceeds {MAX_WRITE_BYTES} bytes")
                target = resolve_inside(self.workspace, task["path"])
                if target.relative_to(self.workspace).as_posix() in {"reports/aegis-report.json", "reports/aegis-report.html", "reports/agent-proposal.json"}:
                    raise ValueError("Task cannot overwrite an AEGIS-owned report")
                if target == self.workspace:
                    raise ValueError("Target must be a file inside workspace")
                if target.exists() and target.is_dir():
                    raise ValueError("Target path is a directory")
                self._atomic_write(target, task["content"])
                return TaskResult(task_id, "PASSED", kind, 0,
                                  f"Wrote {target.relative_to(self.workspace)}", "",
                                  time.monotonic() - started)
            if kind == "python_compile":
                target = resolve_inside(self.workspace, task["path"])
                if not target.is_file() or target.suffix != ".py":
                    raise ValueError("python_compile target must be an existing .py file")
                # Compile in-memory; `py_compile` writes __pycache__ even with -B.
                command = [sys.executable, "-I", "-c",
                           "from pathlib import Path; import sys; p=Path(sys.argv[1]); compile(p.read_text(encoding='utf-8'), str(p), 'exec')",
                           str(target)]
            elif kind == "python_unittest":
                target = resolve_inside(self.workspace, task["path"])
                if not target.exists():
                    raise ValueError("python_unittest target does not exist")
                if target.is_file():
                    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s",
                               str(target.parent), "-p", target.name]
                elif target.is_dir():
                    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(target)]
                else:
                    raise ValueError("python_unittest target must be a file or directory")
            else:
                raise ValueError(f"Unsupported task type: {kind}")
            completed = self._run(command)
            return TaskResult(
                task_id, "PASSED" if completed.returncode == 0 else "FAILED",
                kind, completed.returncode, redact_secrets(completed.stdout[-MAX_OUTPUT_CHARS:]),
                redact_secrets(completed.stderr[-MAX_OUTPUT_CHARS:]), time.monotonic() - started
            )
        except subprocess.TimeoutExpired as exc:
            def safe_text(value):
                if value is None:
                    return ""
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")[-MAX_OUTPUT_CHARS:]
                return str(value)[-MAX_OUTPUT_CHARS:]
            return TaskResult(task_id, "FAILED", kind, None,
                              redact_secrets(safe_text(exc.stdout)), redact_secrets(safe_text(exc.stderr)),
                              time.monotonic() - started, "TIMEOUT")
        except Exception as exc:
            return TaskResult(task_id, "BLOCKED", kind, None, "", "",
                              time.monotonic() - started,
                              f"{type(exc).__name__}: {exc}")
