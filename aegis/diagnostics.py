"""Local static diagnostics and actionable Python traceback hints."""
import ast
import json
import re
from pathlib import Path
from aegis.security import redact_secrets

IGNORE_DIRS = {".git", ".aegis", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "coverage"}


def inspect_workspace(workspace: Path) -> dict:
    root = workspace.expanduser().resolve()
    if not root.is_dir():
        raise OSError(f"Workspace does not exist: {root}")
    python_files, syntax_errors, markers = [], [], []
    for current, dirs, filenames in __import__("os").walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in IGNORE_DIRS and not (Path(current) / name).is_symlink())
        for name in sorted(filenames):
            path = Path(current) / name
            if path.suffix != ".py" or path.is_symlink():
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            rel = path.relative_to(root).as_posix()
            python_files.append(rel)
            try:
                ast.parse(source, filename=rel)
            except SyntaxError as exc:
                syntax_errors.append({"file": rel, "line": exc.lineno, "column": exc.offset, "message": exc.msg})
            for line_no, line in enumerate(source.splitlines(), start=1):
                stripped = line.lstrip()
                if not stripped.startswith(("#", "//", "/*", "*", "<!--")):
                    continue
                match = re.search(r"\b(TODO|FIXME|XXX)\b\s*:?\s*(.*)", line)
                if match:
                    markers.append({"file": rel, "line": line_no, "marker": match.group(1), "note": match.group(2).strip()[:180]})
    findings = []
    for err in syntax_errors:
        findings.append({"severity": "ERROR", "kind": "PYTHON_SYNTAX", **err,
                         "suggestion": "SyntaxError satırındaki girinti, iki nokta, parantez ve tırnakları düzeltin; ardından tekrar inceleyin."})
    for marker in markers:
        findings.append({"severity": "INFO", "kind": marker["marker"], **marker,
                         "suggestion": "Bu notun hâlâ geçerli olup olmadığını ve bir test/kabul ölçütü gerektirip gerektirmediğini doğrulayın."})
    return {"status": "FINDINGS" if syntax_errors else "PASSED", "workspace": str(root),
            "python_files_checked": len(python_files), "python_files": python_files,
            "syntax_errors": syntax_errors, "markers": markers, "findings": findings,
            "limitations": ["AST incelemesi çalışma zamanı davranışını, bağımlılıkları veya güvenlik açıklarını kanıtlamaz.",
                            "TODO/FIXME metinleri hata olarak değil, inceleme notu olarak raporlanır."]}


def diagnose_log(log_path: Path) -> dict:
    path = log_path.expanduser().resolve()
    if not path.is_file():
        raise OSError(f"Log file does not exist: {path}")
    if path.stat().st_size > 2_000_000:
        raise ValueError("Log is larger than the 2 MB analysis limit")
    content = path.read_text(encoding="utf-8", errors="replace")
    # Do not print likely credential values from logs; retain line context only after redaction.
    content = redact_secrets(content)
    hints = [
        (r"ModuleNotFoundError: No module named ['\"]([^'\"]+)", "Eksik Python modülü", "Etkin Python yorumlayıcısında bağımlılığı kurun; doğru sanal ortamın etkin olduğunu doğrulayın."),
        (r"SyntaxError: (.*)", "Python sözdizimi hatası", "Hata satırında girinti, parantez, iki nokta ve tırnakları kontrol edin."),
        (r"IndentationError: (.*)", "Girinti hatası", "Aynı blokta tutarlı boşluk kullanın; sekme ve boşluğu karıştırmayın."),
        (r"NameError: name ['\"]([^'\"]+)['\"] is not defined", "Tanımsız isim", "İsim yazımını, kapsamını ve kullanım öncesi tanımlanıp tanımlanmadığını kontrol edin."),
        (r"ImportError: (.*)", "İçe aktarma hatası", "Modül adını, paket sürümünü ve döngüsel import olasılığını kontrol edin."),
        (r"PermissionError: (.*)", "Dosya/işlem izin hatası", "Hedef yolun, dosya sahibinin ve gereken minimum izinlerin uygun olduğunu doğrulayın; root ile çalıştırmayı varsayılan çözüm yapmayın."),
        (r"FileNotFoundError: (.*)", "Dosya bulunamadı", "Geçerli çalışma dizinini ve mutlak/bağıl yol varsayımını doğrulayın."),
        (r"TimeoutError|timed out|TIMEOUT", "Zaman aşımı", "İşin beklenen süresini, kilitlenmeyi ve ağ/alt süreç durumunu inceleyin; süreyi körlemesine artırmayın."),
        (r"Connection refused|Cannot reach configured model endpoint", "Model bağlantısı kurulamadı", "Yerel sunucunun çalıştığını, temel URL'yi, portu ve model adını kontrol edin."),
        (r"HTTP Error 401|HTTP 401", "Yetkilendirme hatası", "API anahtarının ortam değişkeninde doğru olduğunu ve gerekli izinlere sahip olduğunu doğrulayın."),
    ]
    matched = []
    for pattern, title, suggestion in hints:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            matched.append({"error_type": title, "evidence": match.group(0)[:260], "suggestion": suggestion})
    traceback_lines = [line.strip() for line in content.splitlines() if line.strip().startswith(("File \"", "Traceback", "Error:", "Exception:"))]
    return {"status": "FINDINGS" if matched or traceback_lines else "NO_KNOWN_PATTERN",
            "log_file": str(path), "bytes_read": path.stat().st_size,
            "diagnoses": matched, "traceback_lines": traceback_lines[-20:],
            "note": "Bunlar log tabanlı olası nedenlerdir; düzeltmeyi uygulamaz veya doğruluğunu iddia etmez."}
