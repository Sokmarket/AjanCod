"""Small best-effort secret redactor shared by prompts, reports, and logs.

This is deliberately conservative and is not a substitute for a dedicated DLP scanner.
"""
import re

_SECRET_NAMES = r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|client[_-]?secret)"
_QUOTED_ASSIGNMENT = re.compile(
    rf'''(?i)(["']?\b{_SECRET_NAMES}\b["']?\s*[:=]\s*)(["'])(.*?)\2'''
)
_UNQUOTED_ASSIGNMENT = re.compile(
    rf'''(?im)(["']?\b{_SECRET_NAMES}\b["']?\s*[:=]\s*)([A-Za-z0-9_+=/-]{{6,}})(?=\s*(?:[,;#\r\n]|$))'''
)
_TOKEN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")
_BEARER = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9._~+/=-]+")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    flags=re.IGNORECASE | re.DOTALL,
)


def redact_secrets(text: str, *, allow_unquoted_assignments: bool = True) -> str:
    """Redact common key-value secrets without destroying ordinary code expressions.

    Quoted secret assignments and high-confidence token formats are always masked.
    Unquoted key/value strings are masked when enabled; callers collecting source
    code can disable that heuristic so `token = get_token()` remains intact.
    """
    if not isinstance(text, str):
        return text

    def replace_quoted(match: re.Match) -> str:
        return f"{match.group(1)}{match.group(2)}[REDACTED]{match.group(2)}"

    result = _PRIVATE_KEY.sub("[REDACTED_PRIVATE_KEY]", text)
    result = _QUOTED_ASSIGNMENT.sub(replace_quoted, result)
    if allow_unquoted_assignments:
        result = _UNQUOTED_ASSIGNMENT.sub(lambda match: f'{match.group(1)}"[REDACTED]"', result)
    result = _TOKEN.sub("[REDACTED_TOKEN]", result)
    result = _BEARER.sub(r"\1[REDACTED]", result)
    return result


def redact_object(value):
    """Recursively redact string values before writing logs/reports/state."""
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, dict):
        return {key: redact_object(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_object(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_object(item) for item in value)
    return value
