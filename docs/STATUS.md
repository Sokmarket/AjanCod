# AEGIS PRO v0.3.0 — Status & Evidence

This document separates executed checks from features requiring a real target environment.

## Verification matrix

| Area | Current status | Evidence / limitation |
|---|---|---|
| Unit tests | VERIFIED in current Linux container | `python -m unittest discover -s tests -v` — **44/44 passed** in this build; see `BUILD_EVIDENCE.txt` |
| Python compilation | VERIFIED in current Linux container | `compileall` on `aegis` and `tests`; package wheel build checked |
| Plan validation/order | VERIFIED by unit tests and CLI sample | Does not prove arbitrary user plans are safe |
| Proposal-only agent | VERIFIED with mocked model response | End-to-end provider response is not called in unit tests |
| Test-guided autonomous repair loop | NOT IMPLEMENTED | Model suggestions are applied only on `--apply`; regression testing is a separate user-invoked step |
| Backup/rollback path | Backup creation and path validation tested; rollback failure injection not exhaustive | Best-effort, not a power-loss transaction |
| Secret redaction | VERIFIED for common patterns in tests | Not a universal DLP system |
| Screen permission gate | VERIFIED by unit tests | Physical screen capture and vision endpoint not tested |
| On-demand file watcher | VERIFIED by unit tests | Watches Python file metadata while command runs; not a background service |
| Desktop screen capture | NOT VERIFIED | Requires optional `mss`/Pillow and a supported active desktop |
| Android/Termux capture | NOT VERIFIED | Android screen capture is platform-specific; not promised by this CLI |
| Remote/local model connection | NOT CHECKED | Provider/model endpoint must be configured and reached by the user |
| OS/container sandbox | NOT IMPLEMENTED | Do not run untrusted code as root or on a sensitive host |
| GitHub push/deployment | NOT PERFORMED | A publish helper script is included; no repository was created or pushed by this build |

## Expected local commands

```bash
python -m aegis doctor
python -m aegis --help
python -m aegis validate-plan examples/plan-example.json
python -m aegis run-checks --workspace /tmp/aegis-smoke-workspace
python -m unittest discover -s tests -v
python -m compileall -q aegis tests
```
