"""AEGIS PRO command-line interface."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path
from aegis import __version__
from aegis.agent import run_agent, AgentError, _endpoint_config
from aegis.diagnostics import inspect_workspace, diagnose_log
from aegis.engine import run_plan
from aegis.permissions import get_screen_permission, set_screen_permission
from aegis.plan import load_plan, PlanError
from aegis.screen import analyze_screen
from aegis.watch import watch_workspace


def _print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _screen_permission(args) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    if args.action == "status":
        _print_json({"workspace": str(workspace), "screen_permission": get_screen_permission(workspace)})
        return 0
    if args.action == "revoke":
        status = set_screen_permission(workspace, False)
        _print_json({"status": "REVOKED", "screen_permission": status})
        return 0
    if not sys.stdin.isatty():
        print("PERMISSION_REQUIRED: grant must be confirmed in an interactive terminal.", file=sys.stderr)
        return 3
    print("Ekran okuma izni: AEGIS, bir sonraki ekran analizinde ana monitörün görüntüsünü alacak.")
    print("Görüntü diske kaydedilmez; analiz için yapılandırılmış AEGIS_API_BASE uç noktasına gönderilir.")
    try:
        endpoint, model, _key = _endpoint_config()
        print(f"Uç nokta: {endpoint} | Model: {model}")
    except AgentError as exc:
        print(f"Yapılandırma uyarısı: {exc}")
    answer = input("Bu çalışma alanında ekran analizi özelliğini etkinleştiriyor musunuz? [e/H]: ").strip().lower()
    if answer not in {"e", "evet", "y", "yes"}:
        print("İzin verilmedi; ekran okuma kapalı kaldı.")
        return 3
    status = set_screen_permission(workspace, True)
    _print_json({"status": "GRANTED", "workspace": str(workspace), "screen_permission": status,
                 "note": "Her ekran görüntüsü öncesinde ayrıca onay istenir."})
    return 0


def _screen_analyze(args) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    permission = get_screen_permission(workspace)
    if not permission["enabled"]:
        print("SCREEN_READING_DISABLED: önce `aegis screen-permission grant` komutunu çalıştırın.", file=sys.stderr)
        return 3
    if not sys.stdin.isatty():
        print("CAPTURE_CONFIRMATION_REQUIRED: ekran yakalama interaktif olarak onaylanmalı.", file=sys.stderr)
        return 3
    try:
        endpoint, model, _key = _endpoint_config()
    except AgentError as exc:
        print(f"SCREEN_CONFIG_ERROR: {exc}", file=sys.stderr)
        return 2
    print("UYARI: Ana monitörün ekran görüntüsü alınacak ve analiz için aşağıdaki uç noktaya gönderilecek.")
    print(f"Uç nokta: {endpoint} | Model: {model}")
    print("AEGIS görüntüyü diske kaydetmez. Ekranda parola, özel mesaj veya gizli bilgi varsa devam etmeyin.")
    answer = input("Şimdi ekran görüntüsü alınmasına ve belirtilen uç noktaya gönderilmesine izin veriyor musunuz? [e/H]: ").strip().lower()
    if answer not in {"e", "evet", "y", "yes"}:
        print("İşlem iptal edildi; ekran görüntüsü alınmadı.")
        return 3
    try:
        _print_json(analyze_screen(workspace, args.task, confirmed=True))
    except (RuntimeError, PermissionError, AgentError, OSError) as exc:
        print(f"SCREEN_ANALYSIS_ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="aegis", description="AEGIS PRO — guarded AI software engineering assistant")
    parser.add_argument("--version", action="version", version=f"AEGIS PRO {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="show runtime facts without claiming unperformed checks")
    init = sub.add_parser("init", help="create a workspace")
    init.add_argument("--workspace", default="./workspace")

    validate = sub.add_parser("validate-plan", help="validate and order a JSON plan")
    validate.add_argument("plan")

    run = sub.add_parser("run-plan", help="run allowlisted plan tasks")
    run.add_argument("plan")
    run.add_argument("--workspace", default="./workspace")
    checks = sub.add_parser("run-checks", help="run bundled sample plan")
    checks.add_argument("--workspace", default="./workspace")

    agent = sub.add_parser("agent", help="request a code proposal from an OpenAI-compatible model")
    agent.add_argument("--workspace", default="./workspace")
    agent.add_argument("--task", required=True)
    agent.add_argument("--apply", action="store_true", help="apply files after validating the entire proposal; backups are kept")

    inspect = sub.add_parser("inspect", help="parse Python files and report TODO/FIXME markers")
    inspect.add_argument("--workspace", default=".")
    diagnose = sub.add_parser("diagnose", help="analyze a local error log and suggest likely fixes")
    diagnose.add_argument("--log", required=True, type=Path)

    perm = sub.add_parser("screen-permission", help="grant/revoke persistent opt-in for screen analysis")
    perm.add_argument("action", choices=["grant", "revoke", "status"])
    perm.add_argument("--workspace", default="./workspace")
    screen = sub.add_parser("screen-analyze", help="read the primary desktop screen after consent and suggest fixes")
    screen.add_argument("--workspace", default="./workspace")
    screen.add_argument("--task", default="Identify visible software errors, missing information, and precise suggested fixes.")
    watch = sub.add_parser("watch", help="monitor Python file changes and re-run local diagnostics")
    watch.add_argument("--workspace", default=".")
    watch.add_argument("--interval", type=float, default=5.0, help="poll interval in seconds (1-60)")

    args = parser.parse_args(argv)
    if args.command == "doctor":
        try:
            endpoint, model, api_key = _endpoint_config()
            model_config = {"valid": True, "endpoint": endpoint, "model": model, "api_key_present": bool(api_key), "connection": "NOT_CHECKED"}
        except AgentError as exc:
            model_config = {"valid": False, "error": str(exc), "connection": "NOT_CHECKED"}
        try:
            import mss  # noqa: F401
            from PIL import Image  # noqa: F401
            capture_deps = "AVAILABLE"
        except ImportError:
            capture_deps = "MISSING_OPTIONAL_DEPENDENCIES"
        _print_json({"status": "DIAGNOSTIC_ONLY", "version": __version__, "python_version": sys.version.split()[0],
                     "platform": platform.platform(), "model_provider": model_config,
                     "screen_capture_dependencies": capture_deps,
                     "screen_permission_default": "DISABLED", "container_sandbox": "NOT_IMPLEMENTED",
                     "model_connection": "NOT_CHECKED", "github_push": "NOT_IMPLEMENTED"})
        return 0
    if args.command == "init":
        workspace = Path(args.workspace).expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        readme = workspace / "README.txt"
        if not readme.exists():
            readme.write_text("AEGIS PRO workspace. Review permissions before executing project code.\n", encoding="utf-8")
        print(f"Workspace created: {workspace}")
        return 0
    if args.command == "validate-plan":
        try:
            plan = load_plan(Path(args.plan))
        except PlanError as exc:
            print(f"PLAN_INVALID: {exc}", file=sys.stderr)
            return 2
        print(f"PLAN_VALID: {len(plan['tasks'])} task(s)")
        return 0
    if args.command == "agent":
        try:
            result = run_agent(Path(args.workspace), args.task, args.apply)
        except (AgentError, OSError) as exc:
            print(f"AGENT_ERROR: {exc}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0
    if args.command == "inspect":
        try:
            result = inspect_workspace(Path(args.workspace))
        except OSError as exc:
            print(f"INSPECT_ERROR: {exc}", file=sys.stderr)
            return 2
        _print_json(result)
        return 1 if result["syntax_errors"] else 0
    if args.command == "diagnose":
        try:
            result = diagnose_log(args.log)
        except (OSError, ValueError) as exc:
            print(f"DIAGNOSE_ERROR: {exc}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0 if result["status"] in {"FINDINGS", "NO_KNOWN_PATTERN"} else 1
    if args.command == "screen-permission":
        try:
            return _screen_permission(args)
        except (OSError, ValueError) as exc:
            print(f"SCREEN_PERMISSION_ERROR: {exc}", file=sys.stderr)
            return 2
    if args.command == "screen-analyze":
        return _screen_analyze(args)
    if args.command == "watch":
        def report_change(report, changed):
            print(("CHANGE_DETECTED" if changed else "INITIAL_SCAN") + ": " + str(report["workspace"]))
            print(f"Python files: {report['python_files_checked']} | Syntax errors: {len(report['syntax_errors'])} | Review notes: {len(report['markers'])}")
            for finding in report["findings"]:
                print(f"[{finding['severity']}] {finding['file']}:{finding['line']} {finding['kind']}: {finding['suggestion']}")
            if not report["findings"]:
                print("No syntax errors or TODO/FIXME/XXX comment markers detected.")
        try:
            watch_workspace(Path(args.workspace), args.interval, callback=report_change)
        except KeyboardInterrupt:
            print("\nWATCH_STOPPED: user interrupted.")
            return 0
        except (OSError, ValueError) as exc:
            print(f"WATCH_ERROR: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command in {"run-plan", "run-checks"}:
        if args.command == "run-plan":
            plan_path, workspace = Path(args.plan), Path(args.workspace)
        else:
            plan_path = Path(__file__).resolve().parent.parent / "examples" / "plan-example.json"
            workspace = Path(args.workspace)
        try:
            status, results = run_plan(plan_path, workspace)
        except (PlanError, OSError, ValueError) as exc:
            print(f"RUN_BLOCKED: {exc}", file=sys.stderr)
            return 2
        _print_json({"status": status, "results": results})
        return 0 if status == "PASSED" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
