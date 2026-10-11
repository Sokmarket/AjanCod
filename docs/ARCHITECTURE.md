# AEGIS PRO mimarisi

```text
CLI (aegis/cli.py)
 ├─ Plan path/schema/dependency validation (plan.py)
 ├─ Allowlisted task executor + timeout/output cap (runner.py)
 ├─ Event/state store + JSON/HTML reports (store.py, report.py)
 ├─ Context collection → model adapter → schema/path check → diff/backup/apply (agent.py)
 ├─ Static source / log diagnostics (diagnostics.py)
 ├─ Project change polling (watch.py)
 └─ Consent gate → primary desktop capture in memory → vision-capable model (permissions.py, screen.py)
```

## Main data flow

1. The CLI validates the chosen command and path inputs.
2. Plan commands pass through strict schema validation before tasks are sorted by dependencies.
3. The runner accepts only fixed task types; commands are passed as argument arrays without `shell=True`.
4. The code agent gathers bounded text context, excludes common sensitive file names, masks common inline secret patterns without rewriting ordinary environment lookup expressions, asks a configured model for strict JSON, and validates every target. Redirects from model endpoints are rejected to avoid forwarding project context to a new host.
5. Without `--apply`, the proposal and unified diff are written to the report only. With `--apply`, existing targets are backed up before writes; on failure, rollback is attempted.
6. Screen reading is a separate capability: disabled by default, persistent interactive grant, per-capture interactive confirmation, and explicit endpoint display.
7. Diagnostics distinguish observed syntax/log evidence from suggestions. No module infers that code is correct solely from model wording.

## Deliberate scope

The project intentionally does not execute arbitrary model-returned shell commands, auto-install arbitrary dependencies, push to GitHub, deploy, bypass OS permissions, or claim a sandbox. A future regression-gated repair loop should run in an isolated throwaway environment and require independent tests before marking a repair successful.
