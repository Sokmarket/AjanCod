"""Workspace path policy. This reduces path traversal; it is not an OS sandbox."""
from pathlib import Path
import os


class PathPolicyError(ValueError):
    """A requested file path violates workspace policy."""


def resolve_inside(root: Path, candidate: str | Path) -> Path:
    """Resolve a workspace-local path and reject traversal and symlink components.

    Symlinks are deliberately rejected even when they currently point inside the
    workspace. This avoids surprising write-through behavior. Race-free access
    still requires OS-level isolation / dirfd-based APIs.
    """
    root = root.expanduser().resolve()
    value = Path(candidate).expanduser()
    if not value.is_absolute():
        value = root / value
    # abspath normalizes '..' while preserving symlink components.
    lexical = Path(os.path.abspath(value))
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise PathPolicyError(f"Path escapes workspace: {candidate}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PathPolicyError(f"Symlink paths are not allowed: {candidate}")
    resolved = lexical.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PathPolicyError(f"Path escapes workspace: {candidate}") from exc
    return resolved
