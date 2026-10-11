"""Narrow bridge from the Android UI to the AEGIS Python CLI."""
import contextlib
import io
import json


def run_command_json(raw_args):
    args = json.loads(raw_args)
    if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
        return json.dumps({
            "exit_code": 2,
            "stdout": "",
            "stderr": "Invalid command arguments."
        })

    allowed = {
        "doctor",
        "init",
        "inspect",
        "run-checks",
        "screen-permission",
    }
    if not args or args[0] not in allowed:
        return json.dumps({
            "exit_code": 2,
            "stdout": "",
            "stderr": "Command is not enabled in the Android UI."
        })

    out = io.StringIO()
    err = io.StringIO()
    code = 0
    try:
        from aegis.cli import main
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:
        code = 1
        err.write(f"{type(exc).__name__}: {exc}")

    return json.dumps({
        "exit_code": code,
        "stdout": out.getvalue(),
        "stderr": err.getvalue()
    }, ensure_ascii=False)
