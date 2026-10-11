# Changelog

## v0.3.0 — 2026-10-11

- Added static Python workspace inspection, common traceback/log diagnosis, and an on-demand metadata-based file watcher.
- Improved workspace path policy to reject symlink path components, even when their target is inside the workspace.
- Added atomic writes for text tasks, in-memory compile checks that do not create bytecode cache, and bounded subprocess output capture.
- Added best-effort secret redaction in context, event logs, state and reports; bounded plan/content sizes; HTTPS-only non-local endpoints; and model-request redirect blocking.
- Added configurable OpenAI-compatible model request helper, requiring HTTPS for non-local endpoints.
- Added proposal diffs, preflight validation, per-run backups, and best-effort rollback for code changes.
- Added opt-in desktop primary-monitor screenshot analysis with per-capture user confirmation; screenshots are kept in memory, not saved by AEGIS. Android-wide screen capture is explicitly not claimed by the Python CLI.
- Added logo/app-icon/splash-screen assets in SVG and PNG, tests, docs, and CI workflow.
- Explicitly labels untested provider/screen/sandbox/GitHub capabilities as not verified/not implemented.

## v0.2.0 — inherited baseline

- Strict plan validation and stable dependency ordering.
- Allowlisted plan runner, reports, event/state store, OpenAI-compatible proposal-first model adapter, and curated research documentation.
