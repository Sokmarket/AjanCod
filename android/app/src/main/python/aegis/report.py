"""Evidence-based JSON and HTML execution reports."""
import html
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from aegis.paths import resolve_inside
from aegis.security import redact_object, redact_secrets


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def write_reports(workspace: Path, results: list[dict], overall_status: str) -> tuple[Path, Path]:
    root = workspace.expanduser().resolve()
    json_path = resolve_inside(root, "reports/aegis-report.json")
    html_path = resolve_inside(root, "reports/aegis-report.html")
    if json_path.is_dir() or html_path.is_dir():
        raise OSError("Report destination is a directory")
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "results": redact_object(results),
        "evidence_policy": "Status is based on recorded command/test results; model claims are not evidence.",
    }
    _atomic_write(json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    rows = []
    for result in results:
        cells = [result.get("task_id", ""), result.get("status", ""), result.get("exit_code", ""),
                 redact_secrets(str(result.get("stdout", ""))), redact_secrets(str(result.get("stderr", ""))),
                 redact_secrets(str(result.get("error", "") or ""))]
        rows.append("<tr>" + "".join("<td><pre>" + html.escape(str(value)) + "</pre></td>" for value in cells) + "</tr>")
    page = (
        '<!doctype html><html lang="tr"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>AEGIS PRO Raporu</title>'
        '<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#172033}'
        'table{border-collapse:collapse;width:100%;overflow-wrap:anywhere}'
        'th,td{border:1px solid #ccd3df;padding:.6rem;text-align:left;vertical-align:top}'
        'pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
        '<h1>AEGIS PRO — Çalıştırma Raporu</h1><p><b>Genel durum: '
        + html.escape(overall_status) + '</b></p>'
        '<p>Bu rapor kaydedilen komut ve test sonuçlarını gösterir; hatasızlık garantisi değildir.</p>'
        '<table><thead><tr><th>Görev</th><th>Durum</th><th>Çıkış kodu</th><th>Stdout</th><th>Stderr</th><th>Hata</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></html>'
    )
    _atomic_write(html_path, page)
    return json_path, html_path
